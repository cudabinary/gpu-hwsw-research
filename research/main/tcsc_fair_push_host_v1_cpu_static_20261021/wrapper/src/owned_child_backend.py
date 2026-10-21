"""CPU protocol adapter for the host coordinator, never a CUDA backend."""
from pathlib import Path
import json, time
from owned_cpu_transport import OwnedCPUTransport

class Clock:
    def now(self):
        return time.perf_counter_ns()

class OwnedChildBackend:
    kind = 'CPU_CHILD'

    def __init__(self, root, faults=None):
        self.root = Path(root)
        self.clock = Clock()
        self.transport = None
        self.completed = []
        self.calls = []
        self.faults = faults or {}

    def arm_setup(self, arm, emit, clock):
        emit('CPU_PROTOCOL_FIXTURE_SETUP', arm=arm)
        return {'kind': 'CPU_FIXTURE_NO_BFS_OR_GPU_CHECKS', 'reference_check_ms': 0, 'monitor_preflight_ms': 0}

    def worker(self, index, role, mode, q, emit, clock):
        if self.transport is None:
            self.transport = OwnedCPUTransport(self.root)
        self.calls.append({'index': index, 'mode': mode, 'q': q})
        row = self.transport.run(index, mode, q, emit, case=self.faults.get(index, 'success'))
        if row['post_exit_memory_coverage'] != 'OWNED_PROCESS_PEAK_COUNTERS_AVAILABLE':
            raise RuntimeError('OWNED_CPU_PEAK_COVERAGE_UNKNOWN')
        emit('MEMORY_SAMPLE', device_requested_bytes=0, builder_account_peak_bytes=0,
             owned_host_peak_upper_bound_bytes=row['post_exit_private_peak_sum_bytes'],
             coverage='OS_OWNED_PROCESS_PEAK_COUNTERS_NOT_DRIVER_MEMORY')
        self.completed.append(row)
        guards = {k: True for k in ['CPU_fixture_shape', 'CPU_fixture_checksum', 'PID_ACK',
                                   'watchdog', 'CPU_process_observations', 'CPU_release_marker', 'owned_process_exited']}
        metrics = {'kind': 'CPU_PROTOCOL_FIXTURE_NO_ALGORITHM_NOT_GPU', 'cpu_reverse_build_ms': 0,
                   'cpu_static_bound_ms': 0, 'algorithm_preparation_ms': 0,
                   'static_bound_setup_ms': 0, 'context_setup_transfer_ms': 'UNKNOWN_NOT_APPLICABLE_CPU_FIXTURE',
                   'cpu_reference_and_work_replay_ms': 0, 'post_batch_validation_ms': 0,
                   'H2D_only_ms': 'UNKNOWN', 'allocation_only_ms': 'UNKNOWN'}
        return {'kind': 'CPU_OWNED_CHILD_NOT_GPU_OR_BFS', 'mode': mode, 'q': q, 'guards': guards,
                'init_only_cancel_tests': int(q == 3), 'metrics': metrics,
                'memory': {'kind': 'OWNED_CPU_COUNTERS', 'sampled_private_peak_sum_bytes': row['sampled_peak_private_commit_sum_bytes'],
                           'post_exit_peak_private_sum_bytes': row['post_exit_private_peak_sum_bytes'],
                           'lifetime_peak_coverage': row['post_exit_memory_coverage'],
                           'OS_driver_physical_bytes': 'UNKNOWN_NOT_MEASURED'}}

    def cleanup(self, arm, failed, emit, clock):
        receipts = [json.loads(p.read_text()) for p in self.root.glob('*/TRANSPORT_RECEIPT.json')]
        okay = len(receipts) == len(self.calls) and all(x['owned_process_exited'] and x.get('watchdog_retirement') != 'UNCONFIRMED' for x in receipts)
        emit('CPU_FIXTURE_CLEANUP', arm=arm)
        return {'kind': 'CPU_PROCESS_ONLY_NO_CUDA_CONTEXT', 'owned_context_retirement_confirmed': okay, 'cleanup_ms': 'NOT_SEPARATELY_TIMED'}

    def gap(self, seconds, clock):
        if seconds != 0:
            raise RuntimeError('CPU_FIXTURE_REQUIRES_ZERO_GAP_NOT_GPU_PROTOCOL')
