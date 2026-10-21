"""Real owned CPU-child transport; no arbitrary commands, GPU query or dispatch."""
from pathlib import Path
import ctypes, hashlib, json, os, subprocess, sys, time
from ctypes import wintypes as W
import watchdog_support

class Counters(ctypes.Structure):
    _fields_ = [('cb', W.DWORD), ('PageFaultCount', W.DWORD)] + [(x, ctypes.c_size_t) for x in
        ['PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
         'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage']]

class OwnedMemory:
    def __init__(self):
        self.api = ctypes.WinDLL('psapi', use_last_error=True).GetProcessMemoryInfo
        self.api.argtypes = [W.HANDLE, ctypes.POINTER(Counters), W.DWORD]
        self.api.restype = W.BOOL
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.GetCurrentProcess.restype = W.HANDLE
        self.current = k.GetCurrentProcess()

    def sample(self, members):
        result = {}
        for name, handle in [('coordinator', self.current), *members]:
            out = Counters()
            out.cb = ctypes.sizeof(out)
            if not self.api(W.HANDLE(int(handle)), ctypes.byref(out), out.cb):
                raise OSError(ctypes.get_last_error(), 'OWNED_MEMORY_COUNTER_UNAVAILABLE_' + name)
            result[name] = {'private_commit_bytes': out.PrivateUsage, 'peak_private_commit_bytes': out.PeakPagefileUsage,
                            'working_set_bytes': out.WorkingSetSize, 'peak_working_set_bytes': out.PeakWorkingSetSize}
        return result

class OwnedCPUTransport:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.memory = OwnedMemory()

    def run(self, index, mode, q, emit, case='success', timeout_seconds=3, host_cap=1 << 30):
        if case not in ['success', 'nonzero', 'hang', 'cancel', 'bad_ready', 'bad_output', 'missing_release']:
            raise ValueError('CPU_FIXTURE_CASE_ONLY')
        r = self.root / f'{index:02d}'
        r.mkdir(exist_ok=False)
        child = watchdog = None
        samples = []
        status = {'kind': 'OWNED_CPU_CHILD_NO_CUDA', 'case': case, 'success': False,
                  'actual_GPU_queries_or_dispatches': 0, 'post_exit_memory_coverage': 'UNKNOWN'}
        log = (r / 'stdout.log').open('xb')
        err = (r / 'stderr.log').open('xb')
        try:
            env = {k: v for k, v in os.environ.items() if not k.startswith('TCSC_')}
            command = [sys.executable, str(Path(__file__).with_name('cpu_child_fixture.py')),
                       '--directory', str(r), '--case', case, '--mode', str(mode), '--q', str(q)]
            (r / 'command.json').write_text(json.dumps({'argv': command, 'GPU_permits_inherited': False}, indent=2))
            child = subprocess.Popen(command, env=env, stdout=log, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
            emit('POPEN_RETURN')
            watchdog = watchdog_support.start(child, r / 'watchdog.json', watchdog_support.now_tick() + int(timeout_seconds*1000))
            acknowledged = False
            began = time.monotonic()
            while child.poll() is None:
                emit('OBSERVE_ENTER', observation_kind='CPU_OWNED_PROCESS_ONLY')
                sample = self.memory.sample([('child', child._handle), ('watchdog', watchdog._handle)])
                samples.append(sample)
                peak = sum(x['peak_private_commit_bytes'] for x in sample.values())
                if peak > host_cap:
                    raise RuntimeError('OWNED_HOST_BUDGET')
                emit('MEMORY_SAMPLE', device_requested_bytes=0, builder_account_peak_bytes=0,
                     owned_host_peak_upper_bound_bytes=peak, actual_OS_sample=sample,
                     coverage='SAMPLED_TO_THIS_POINT_NOT_DRIVER_MEMORY')
                emit('OBSERVE_EXIT', observation_kind='CPU_OWNED_PROCESS_ONLY')
                state = json.loads((r / 'watchdog.json').read_text()) if (r / 'watchdog.json').exists() else None
                if watchdog.poll() is not None and child.poll() is None:
                    raise RuntimeError('INDEPENDENT_CPU_WATCHDOG_EXITED')
                if not acknowledged and (r / 'ready').exists() and state and state['status'] == 'WATCHING':
                    if int((r / 'ready').read_text()) != child.pid:
                        raise RuntimeError('CPU_READY_PID_MISMATCH')
                    emit('READY_OBSERVED')
                    (r / 'ack').write_text(str(child.pid))
                    emit('ACK_WRITTEN')
                    acknowledged = True
                if case == 'cancel' and acknowledged:
                    raise RuntimeError('CPU_PARENT_CANCELLED')
                if time.monotonic() - began > timeout_seconds + 1:
                    raise RuntimeError('CPU_PARENT_WATCHDOG_BACKSTOP')
                time.sleep(.01)
            emit('CHILD_EXIT_OBSERVED')
            watchdog.wait(timeout=3)
            wd = json.loads((r / 'watchdog.json').read_text())
            if child.returncode or not acknowledged or watchdog.returncode or wd['status'] != 'CHILD_EXITED':
                raise RuntimeError('CPU_CHILD_OR_WATCHDOG_FAILURE_' + str(wd['status']))
            log.close()
            err.close()
            if 'CPU_CHILD_RELEASED_NO_CUDA' not in (r / 'stderr.log').read_text():
                raise RuntimeError('CPU_RELEASE_MARKER_MISSING')
            emit('RETIREMENT_CONFIRMED', kind='CPU_PROCESS_EXIT_NOT_CUDA_RETIREMENT')
            raw = json.loads((r / 'result.json').read_text())
            expected = {'kind': 'CPU_CHILD_PROTOCOL_NOT_BFS', 'mode': mode, 'q': q,
                        'logical_slots': list(range(q)), 'simulated_init_cancel': int(q == 3)}
            digest = hashlib.sha256(json.dumps(raw['payload'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            if raw['payload'] != expected or raw['sha256'] != digest:
                raise RuntimeError('CPU_FIXTURE_OUTPUT_MISMATCH')
            try:
                status['post_exit_owned_memory'] = self.memory.sample([('child', child._handle), ('watchdog', watchdog._handle)])
                status['post_exit_memory_coverage'] = 'OWNED_PROCESS_PEAK_COUNTERS_AVAILABLE'
                status['post_exit_private_peak_sum_bytes'] = sum(x['peak_private_commit_bytes'] for x in status['post_exit_owned_memory'].values())
                if status['post_exit_private_peak_sum_bytes'] > host_cap:
                    raise RuntimeError('OWNED_HOST_BUDGET_AT_EXIT')
            except OSError as problem:
                status['post_exit_memory_coverage'] = 'UNKNOWN_UNAVAILABLE_' + str(getattr(problem, 'winerror', None) or problem.errno)
            status['sampled_peak_private_commit_sum_bytes'] = max(sum(x['peak_private_commit_bytes'] for x in s.values()) for s in samples)
            status['sample_count'] = len(samples)
            emit('OUTPUT_VALIDATED', kind='CPU_PROTOCOL_PAYLOAD_NOT_BFS_DISTANCE')
            status['success'] = True
            return status
        except BaseException as problem:
            status['reason'] = str(problem)
            raise
        finally:
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    status['owned_process_retirement'] = 'UNCONFIRMED'
            if watchdog is not None:
                try:
                    watchdog.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    status['watchdog_retirement'] = 'UNCONFIRMED'
            status['owned_process_exited'] = child is not None and child.poll() is not None
            status['child_returncode'] = child.returncode if child is not None else None
            status['watchdog_returncode'] = watchdog.returncode if watchdog is not None else None
            status['owned_memory_samples'] = samples
            status['retirement_scope'] = 'OWNED_OS_PROCESS_ONLY_CUDA_RETIREMENT_UNVERIFIED'
            status['raw_files_preserved'] = True
            for handle in [log, err]:
                if not handle.closed:
                    handle.close()
            with (r / 'TRANSPORT_RECEIPT.json').open('x') as receipt:
                json.dump(status, receipt, indent=2)
