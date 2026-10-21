"""Virtual clock and synthetic reports only. No process or device API."""

class VirtualClock:
    def __init__(self):
        self.ns = 0

    def now(self):
        return self.ns

    def advance_ms(self, value):
        self.ns += int(value * 1_000_000)

class MockBackend:
    kind = 'CPU_MOCK'

    def __init__(self, fault=None, fault_worker=2):
        self.clock = VirtualClock()
        self.fault, self.fault_worker = fault, fault_worker
        self.calls, self.cleanup_calls = [], []

    def arm_setup(self, arm, emit, clock):
        clock.advance_ms(10)
        emit('MOCK_REFERENCE_PREPARATION', arm=arm)
        clock.advance_ms(10)
        emit('MOCK_MONITOR_PREFLIGHT', arm=arm)
        return {'kind': 'SYNTHETIC_NOT_MEASURED', 'reference_check_ms': 10,
                'monitor_preflight_ms': 10}

    def worker(self, index, role, mode, q, emit, clock):
        self.calls.append({'index': index, 'role': role, 'mode': mode, 'q': q})
        fault = self.fault if index == self.fault_worker else None
        emit('OBSERVE_ENTER')
        clock.advance_ms(1)
        emit('OBSERVE_EXIT')
        memory = {'device_requested_bytes': (275124 if mode == 7 else 501580) if q == 32 else (208 if mode == 7 else 312),
                  'builder_account_peak_bytes': (512 if mode == 7 else 291480) if q == 32 else (8 if mode == 7 else 208),
                  'owned_host_peak_upper_bound_bytes': 100000000,
                  'actual_OS_peak': 'UNKNOWN_MOCK_NO_OS_QUERY',
                  'driver_physical_bytes': 'UNKNOWN', 'kind': 'SYNTHETIC'}
        changes = {'device_budget': ('device_requested_bytes', (32 << 20) + 1),
                   'builder_budget': ('builder_account_peak_bytes', (32 << 20) + 1),
                   'host_budget': ('owned_host_peak_upper_bound_bytes', (1 << 30) + 1),
                   'memory_unknown': ('owned_host_peak_upper_bound_bytes', None)}
        if fault in changes:
            key, value = changes[fault]
            memory[key] = value
        emit('MEMORY_SAMPLE', **memory)
        if fault == 'storage_budget':
            emit('RAW_RESERVATION', bytes=128 << 20)
        if fault == 'sample_budget':
            for _ in range(121):
                emit('OBSERVE_EXIT')
        if fault in ['watchdog', 'arm_deadline', 'campaign_deadline']:
            clock.advance_ms({'watchdog': 20001, 'arm_deadline': 90001, 'campaign_deadline': 600001}[fault])
            emit('TIME_BOUNDARY')
        if fault == 'clock':
            clock.advance_ms(-1)
            emit('TIME_BOUNDARY')
        clock.advance_ms(1)
        emit('POPEN_RETURN')
        clock.advance_ms(10)
        emit('READY_OBSERVED')
        if fault == 'wrong_order':
            emit('CHILD_EXIT_OBSERVED')
        clock.advance_ms(1)
        emit('ACK_WRITTEN')
        if fault in ['error', 'cancel']:
            emit('MOCK_FAILURE', reason=fault)
            raise RuntimeError('SYNTHETIC_' + fault.upper())
        if fault == 'interrupt':
            emit('MOCK_FAILURE', reason=fault)
            raise KeyboardInterrupt('SYNTHETIC_INTERRUPT')
        clock.advance_ms(50)
        emit('CHILD_EXIT_OBSERVED')
        clock.advance_ms(3)
        emit('RETIREMENT_CONFIRMED')
        clock.advance_ms(4)
        emit('OUTPUT_VALIDATED')
        guards = {k: True for k in ['Cplusplus_full_array', 'Python_full_array', 'PID_ACK',
                                   'watchdog', 'telemetry', 'context_release_marker', 'owned_PID_absent']}
        if fault == 'mismatch':
            guards['Python_full_array'] = False
        if fault == 'guard':
            guards['watchdog'] = False
        if fault == 'retirement':
            guards['owned_PID_absent'] = False
        metrics = {'kind': 'SYNTHETIC_NOT_GPU_TIMING', 'graph_load_ms': 2,
                   'cpu_reverse_build_ms': 0 if mode == 7 else 0.3, 'static_bound_setup_ms': 0,
                   'cpu_static_bound_ms': 0.1 if mode == 7 else 0,
                   'algorithm_preparation_ms': 0.1 if mode == 7 else 0.3,
                   'cpu_reference_and_work_replay_ms': 5,
                   'context_setup_transfer_ms': 20,
                   'H2D_only_ms': 'UNKNOWN', 'allocation_only_ms': 'UNKNOWN',
                   'owned_ready_prefix_ms': {str(k): k * 0.5 for k in [1, 2, 8, 32]},
                   'sum_stream_interval_ms_not_busy': 14,
                   'sum_output_allocation_D2H_ms': 1,
                   'post_batch_validation_ms': 0.1}
        return {'kind': 'SYNTHETIC_NO_BFS_EXECUTION', 'mode': mode, 'q': q, 'guards': guards,
                'init_only_cancel_tests': 0 if fault == 'missing_cancel' else int(q == 3),
                'metrics': metrics, 'memory': memory}

    def cleanup(self, arm, failed, emit, clock):
        self.cleanup_calls.append({'arm': arm, 'failed': failed})
        if self.fault == 'cleanup' and not failed:
            raise RuntimeError('SYNTHETIC_CLEANUP_FAILURE')
        clock.advance_ms(3)
        emit('MOCK_CLEANUP', arm=arm)
        return {'kind': 'SYNTHETIC_NOT_MEASURED', 'owned_context_retirement_confirmed': self.fault != 'retirement',
                'cleanup_ms': 3}

    def gap(self, seconds, clock):
        clock.advance_ms(seconds * 1000)
