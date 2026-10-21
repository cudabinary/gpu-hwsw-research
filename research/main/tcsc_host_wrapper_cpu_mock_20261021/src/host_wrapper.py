"""Append-only host coordinator. The only bound backend is a CPU mock.

No CUDA, process launcher, device query, compiler or old runner is imported.
"""
from pathlib import Path
import argparse, copy, hashlib, json, time

ROOT = Path(__file__).resolve().parents[1]
MARKERS = ['POPEN_RETURN', 'READY_OBSERVED', 'ACK_WRITTEN',
           'CHILD_EXIT_OBSERVED', 'RETIREMENT_CONFIRMED', 'OUTPUT_VALIDATED']
GUARDS = ['Cplusplus_full_array', 'Python_full_array', 'PID_ACK', 'watchdog',
          'telemetry', 'context_release_marker', 'owned_PID_absent']

class Stop(RuntimeError):
    pass

class GPUDispatchDisabled(Stop):
    pass

class RealClock:
    def now(self):
        return time.perf_counter_ns()

def backend_for(name):
    if name != 'cpu-mock':
        raise GPUDispatchDisabled('GPU_DISPATCH_DISABLED_UNBOUND_ADAPTER')
    from mock_backend import MockBackend
    return MockBackend()

def validate_plan(p):
    if p['status'] != 'CPU_MOCK_ONLY_LIVE_UNBOUND' or p['execution_authorized'] or p['gpu_adapter_implemented']:
        raise Stop('LIVE_PERMISSION_OR_ADAPTER_NOT_ALLOWED')
    if p['contract'] != 'ISOLATION_UNVERIFIED' or p['arm_target_modes'] != [7, 5, 5, 7]:
        raise Stop('FIXED_CONTRACT_OR_ORDER')
    if [(x['mode'], x['q']) for x in p['required_smoke_per_arm']] != [(7, 3), (5, 3)]:
        raise Stop('MANDATORY_SMOKE_GATE')
    if (p['maximum_CUDA_workers'], p['maximum_full_BFS_arrays'], p['maximum_init_only_cancellations']) != (12, 152, 8):
        raise Stop('FIXED_COUNT_BUDGET')
    if p['optional_extra_smoke'] or p['warmups'] or p['automatic_retries']:
        raise Stop('NO_EXTRA_WORK_OR_RETRY')
    if p['memory_per_arm']['device_application_cap_bytes'] != 32 << 20 or p['memory_per_arm']['CPU_builder_account_cap_bytes'] != 32 << 20:
        raise Stop('COMMON_APPLICATION_MEMORY_CAPS')
    if p['memory_per_arm']['proposed_owned_host_group_conservative_peak_budget_bytes'] != 1 << 30:
        raise Stop('COMMON_HOST_MEMORY_BUDGET')
    s = p['safety']
    if (s['start_free_MiB'], s['run_free_MiB'], s['temperature_limit_exclusive_C'], s['telemetry_freshness_ms'], s['telemetry_command_timeout_seconds']) != (2048, 1536, 78, 3000, 2):
        raise Stop('FIXED_SAFETY_THRESHOLDS')
    if not all(s[k] for k in ['required_full_array_Cplusplus_and_Python', 'required_init_only_cancel_checks', 'required_PID_ACK_watchdog_context_retirement', 'stop_on_observable_foreign_research_CUDA']):
        raise Stop('REQUIRED_SAFETY_POLICY')
    if s['protected_or_foreign_process_module_memory_queries'] or s['OS_security_clock_driver_changes']:
        raise Stop('FORBIDDEN_ENVIRONMENT_ACTION')
    if not p['CPU_checks_in_primary_arm_cold'] or not p['required_smoke_and_logging_in_primary_arm_cold']:
        raise Stop('HIDDEN_COLD_CHECK_COST')
    if p['host_minus_event_is_pure_host_time'] or p['driver_ready_is_resident_CSR_ready']:
        raise Stop('INVALID_TIMER_INTERPRETATION')

class Campaign:
    def __init__(self, plan, output, backend, clock=None):
        validate_plan(plan)
        if backend.kind != 'CPU_MOCK':
            raise GPUDispatchDisabled('GPU_DISPATCH_DISABLED_UNBOUND_ADAPTER')
        self.plan, self.out, self.backend = copy.deepcopy(plan), Path(output), backend
        self.clock = clock or RealClock()
        self.out.mkdir(parents=True, exist_ok=False)
        self.file = (self.out / 'ledger.jsonl').open('x', encoding='utf-8')
        self.started = self.clock.now()
        self.previous = self.started
        self.arm_started = self.worker_started = None
        self.arm_samples = self.samples = self.launched = self.bfs = self.cancels = 0
        self.state, self.workers = 'NEW', []

    def save(self, name, value, emergency=False):
        encoded = json.dumps(value, indent=2)
        self.quota(len(encoded.encode()), emergency)
        with (self.out / name).open('x', encoding='utf-8') as f:
            f.write(encoded)

    def quota(self, reserve=0, emergency=False):
        used = sum(p.stat().st_size for p in self.out.rglob('*') if p.is_file())
        cap = self.plan['maximum_raw_output_bytes_campaign'] - (0 if emergency else 1 << 20)
        if reserve < 0 or used + reserve > cap:
            raise Stop('RAW_STORAGE_BUDGET')

    def emit(self, event, **data):
        now = self.clock.now()
        if now < self.previous:
            raise Stop('NONMONOTONIC_HOST_CLOCK')
        self.previous = now
        row = {'kind': 'CPU_MOCK_ONLY', 'host_ns': now, 'event': event, **data}
        encoded = json.dumps(row) + '\n'
        self.quota(len(encoded.encode()))
        self.file.write(encoded)
        self.file.flush()
        if (now - self.started) / 1e9 > self.plan['campaign_wall_cap_seconds_including_gaps']:
            raise Stop('CAMPAIGN_DEADLINE')
        if self.arm_started is not None and (now - self.arm_started) / 1e9 > self.plan['arm_wall_cap_seconds_including_cleanup']:
            raise Stop('ARM_DEADLINE')
        if self.worker_started is not None and (now - self.worker_started) / 1e9 > self.plan['child_watchdog_seconds']:
            raise Stop('CHILD_WATCHDOG')
        if event == 'OBSERVE_EXIT':
            self.arm_samples += 1
            self.samples += 1
            if self.arm_samples > self.plan['maximum_management_samples_per_arm'] or self.samples > self.plan['maximum_management_samples_campaign']:
                raise Stop('OBSERVATION_BUDGET')
        if event == 'RAW_RESERVATION':
            self.quota(data['bytes'])
        if event == 'MEMORY_SAMPLE':
            m = self.plan['memory_per_arm']
            for key, cap in [('device_requested_bytes', m['device_application_cap_bytes']),
                             ('builder_account_peak_bytes', m['CPU_builder_account_cap_bytes']),
                             ('owned_host_peak_upper_bound_bytes', m['proposed_owned_host_group_conservative_peak_budget_bytes'])]:
                value = data.get(key)
                if not isinstance(value, int) or value < 0 or value > cap:
                    raise Stop('MEMORY_BUDGET_OR_COVERAGE_' + key)

    def worker(self, arm, role, mode, q):
        if self.state != 'RUNNING' or self.launched >= self.plan['maximum_CUDA_workers']:
            raise Stop('DISPATCH_STATE_OR_COUNT')
        index = self.launched
        self.launched += 1
        self.worker_started = self.clock.now()
        began = self.worker_started
        self.emit('WORKER_BEGIN', arm=arm, index=index, role=role, mode=mode, q=q)
        marks = {}
        def observed(event, **data):
            self.emit(event, arm=arm, index=index, **data)
            if event in MARKERS:
                if event in marks or MARKERS[len(marks)] != event:
                    raise Stop('WORKER_BOUNDARY_ORDER')
                marks[event] = self.clock.now()
        response = self.backend.worker(index, role, mode, q, observed, self.clock)
        self.worker_started = None
        self.save(f'{index:02d}.response.json', response)
        if list(marks) != MARKERS or response['mode'] != mode or response['q'] != q:
            raise Stop('RESULT_BOUNDARY_OR_IDENTITY')
        if not all(response['guards'].get(k) is True for k in GUARDS):
            raise Stop('REQUIRED_GUARD_FAILED')
        if response['init_only_cancel_tests'] != int(q == 3):
            raise Stop('CANCEL_CONTRACT')
        self.bfs += q
        self.cancels += int(q == 3)
        record = {'arm': arm, 'role': role, 'mode': mode, 'q': q,
                  'synthetic_target_envelope_ns': marks['OUTPUT_VALIDATED'] - began,
                  'existing_child_metrics': response['metrics'],
                  'memory': response['memory'], 'sample_kind': 'CPU_MOCK_NOT_GPU_MEASUREMENT'}
        self.workers.append(record)
        return record

    def run(self):
        if self.state != 'NEW':
            raise Stop('NO_RESUME_OR_RETRY')
        self.state = 'RUNNING'
        arms = []
        try:
            self.save('PLAN_USED.json', self.plan)
            for arm, mode in enumerate(self.plan['arm_target_modes']):
                self.arm_started, self.arm_samples = self.clock.now(), 0
                self.emit('ARM_BEGIN', arm=arm, target_mode=mode)
                setup = self.backend.arm_setup(arm, self.emit, self.clock)
                for smoke in self.plan['required_smoke_per_arm']:
                    self.worker(arm, 'REQUIRED_SMOKE', smoke['mode'], smoke['q'])
                self.emit('SMOKE_GATE_COMPLETE', arm=arm)
                target = self.worker(arm, 'TARGET_Q32', mode, 32)
                cleanup = self.backend.cleanup(arm, False, self.emit, self.clock)
                if not cleanup['owned_context_retirement_confirmed']:
                    raise Stop('UNCONFIRMED_CONTEXT_RETIREMENT')
                self.emit('ARM_COMPLETE', arm=arm)
                arms.append({'arm': arm, 'mode': mode, 'synthetic_cold_arm_ns': self.clock.now() - self.arm_started,
                             'mandatory_arm_setup_and_checks': setup, 'cleanup': cleanup,
                             'required_smoke_envelopes_ns': sum(w['synthetic_target_envelope_ns'] for w in self.workers if w['arm'] == arm and w['role'] == 'REQUIRED_SMOKE'),
                             'target_process_envelope_ns': target['synthetic_target_envelope_ns'],
                             'algorithm_preparation_CPU_reverse_ms': target['existing_child_metrics']['cpu_reverse_build_ms'],
                             'algorithm_preparation_static_metadata_ms_inside_native_setup': target['existing_child_metrics']['static_bound_setup_ms'],
                             'mixed_native_setup_ACK_alloc_H2D_ms': target['existing_child_metrics']['context_setup_transfer_ms'],
                             'target_CPU_reference_replay_ms': target['existing_child_metrics']['cpu_reference_and_work_replay_ms'],
                             'target_post_batch_validation_ms': target['existing_child_metrics']['post_batch_validation_ms'],
                             'target_experiment_check_ms': target['existing_child_metrics']['cpu_reference_and_work_replay_ms'] + target['existing_child_metrics']['post_batch_validation_ms'],
                             'cost_components_overlap_not_additive': True})
                self.arm_started = None
                if arm != 3:
                    self.backend.gap(self.plan['gap_seconds_after_every_completed_arm'], self.clock)
                    self.emit('GAP_COMPLETE', arm=arm)
            self.emit('CAMPAIGN_COMPLETE')
            self.state = 'COMPLETE'
            self.save('RECEIPT.json', {'status': 'CPU_MOCK_COMPLETE_NOT_GPU_PASS', 'arms': arms,
                'workers': self.workers, 'simulated_workers': self.launched, 'simulated_BFS': self.bfs,
                'simulated_init_only_cancels': self.cancels, 'actual_GPU_dispatches': 0,
                'fair_no_reverse_Push_cold_baseline': 'ABSENT_FROM_UNCHANGED_BINARY',
                'internal_H2D_allocation_split': 'UNKNOWN', 'OS_driver_physical_peak': 'UNKNOWN'})
        except BaseException as error:
            self.state = 'STOPPED'
            self.worker_started = self.arm_started = None
            try:
                cleanup = self.backend.cleanup(None, True, lambda *a, **k: None, self.clock)
            except BaseException as cleanup_error:
                cleanup = {'failure': str(cleanup_error), 'owned_context_retirement_confirmed': False}
            self.save('STOP.json', {'status': 'CPU_MOCK_STOP_NO_FOLLOWUP', 'reason': str(error),
                'simulated_workers_started': self.launched, 'workers_validated': len(self.workers),
                'cleanup': cleanup, 'resume_allowed': False, 'actual_GPU_dispatches': 0}, emergency=True)
        finally:
            self.file.close()
        return self.state

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu-mock', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.cpu_mock:
        raise GPUDispatchDisabled('GPU_DISPATCH_DISABLED_UNBOUND_ADAPTER')
    backend = backend_for('cpu-mock')
    plan = json.loads((ROOT / 'config/PLAN_CPU_ONLY.json').read_text())
    result = Campaign(plan, args.output, backend, backend.clock).run()
    print(json.dumps({'status': result, 'kind': 'CPU_MOCK_ONLY', 'actual_GPU_dispatches': 0}))

if __name__ == '__main__':
    main()
