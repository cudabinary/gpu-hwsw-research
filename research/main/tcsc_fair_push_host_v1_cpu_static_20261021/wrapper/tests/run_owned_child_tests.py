"""Bounded real CPU-owned-process tests; never runs a GPU process or query."""
from pathlib import Path
import json, sys, time

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'src'))
from host_wrapper import Campaign, backend_for
from owned_cpu_transport import OwnedCPUTransport

def main():
    R = P / 'results/CPU_OWNED_CHILD_TESTS'
    R.mkdir(parents=True, exist_ok=False)
    plan = json.loads((P / 'config/PLAN_CPU_ONLY.json').read_text())
    plan['gap_seconds_after_every_completed_arm'] = 0
    plan['CPU_protocol_fixture_only'] = True
    backend = backend_for('cpu-child-fixture', R / 'campaign')
    campaign = Campaign(plan, R / 'campaign', backend, backend.clock)
    assert campaign.run() == 'COMPLETE'
    assert len(backend.calls) == 12
    assert all(x['owned_process_exited'] and x['post_exit_memory_coverage'] == 'OWNED_PROCESS_PEAK_COUNTERS_AVAILABLE' for x in backend.completed)
    checks = ['real_CPU_children_connected_through_coordinator', 'post_exit_owned_process_peak_counters_available']
    failures = [
        ('nonzero', 3, 1 << 30, 'CPU_CHILD_OR_WATCHDOG_FAILURE'),
        ('hang', .5, 1 << 30, 'CPU_CHILD_OR_WATCHDOG_FAILURE'),
        ('cancel', 3, 1 << 30, 'CPU_PARENT_CANCELLED'),
        ('bad_ready', 3, 1 << 30, 'CPU_READY_PID_MISMATCH'),
        ('bad_output', 3, 1 << 30, 'CPU_FIXTURE_OUTPUT_MISMATCH'),
        ('missing_release', 3, 1 << 30, 'CPU_RELEASE_MARKER_MISSING'),
        ('success', 3, 1, 'OWNED_HOST_BUDGET')]
    for index, (case, deadline, cap, expected) in enumerate(failures):
        directory = R / f'negative_{index:02d}_{case}'
        transport = OwnedCPUTransport(directory)
        events = []
        try:
            transport.run(0, 7, 3, lambda event, **data: events.append({'host_ns': time.perf_counter_ns(), 'event': event, **data}),
                          case=case, timeout_seconds=deadline, host_cap=cap)
        except RuntimeError as problem:
            assert expected in str(problem), (case, str(problem))
        else:
            raise AssertionError('CPU_NEGATIVE_NOT_REJECTED_' + case)
        row = json.loads((directory / '00/TRANSPORT_RECEIPT.json').read_text())
        assert not row['success'] and row['owned_process_exited'] and row['actual_GPU_queries_or_dispatches'] == 0
        assert (directory / '00/stderr.log').is_file()
        if case == 'hang':
            assert json.loads((directory / '00/watchdog.json').read_text())['status'] == 'DEADLINE_CHILD_TERMINATED'
        (directory / 'events.json').write_text(json.dumps(events, indent=2))
        checks.append('real_CPU_' + case + '_rejected_and_owned_process_retired')
    result = {'status': 'CPU_OWNED_CHILD_TESTS_PASS', 'checks': checks, 'check_count': len(checks),
        'CPU_fixture_processes': 19, 'independent_watchdog_processes': 19,
        'actual_GPU_queries_or_dispatches': 0, 'actual_GPU_accuracy_or_sanitizer_tests': 0,
        'GPU_PID_or_engine_monitor_validation': 'NOT_EXECUTED_UNKNOWN',
        'OS_memory_scope': 'coordinator + its CPU child + its watchdog only',
        'driver_physical_peak': 'UNKNOWN', 'CPU_fixture_payloads_are_not_BFS': True}
    (R / 'SUMMARY.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
