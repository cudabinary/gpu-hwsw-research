"""Small deterministic mock campaign tests, without child/device APIs."""
from pathlib import Path
import argparse, copy, hashlib, json, sys

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'src'))
from host_wrapper import Campaign, Stop, GPUDispatchDisabled, backend_for
from mock_backend import MockBackend

def digest(root):
    return {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in root.rglob('*') if f.is_file()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('results/CPU_MOCK_TESTS'))
    args = parser.parse_args()
    plan = json.loads((P / 'config/PLAN_CPU_ONLY.json').read_text())
    base = P / args.output
    base.mkdir(parents=True, exist_ok=False)
    passed = []
    disabled = base / 'GPU_MUST_NOT_START'
    try:
        backend_for('gpu')
    except GPUDispatchDisabled:
        assert not disabled.exists()
        passed.append('default_GPU_backend_unconditionally_disabled')
    else:
        raise AssertionError('GPU_BACKEND_MUST_STAY_UNBOUND')
    backend = MockBackend()
    runner = Campaign(plan, base / 'nominal', backend, backend.clock)
    assert runner.run() == 'COMPLETE'
    assert len(backend.calls) == 12
    assert [x['mode'] for x in backend.calls if x['role'] == 'TARGET_Q32'] == [7, 5, 5, 7]
    for arm in range(4):
        assert [(x['role'], x['mode']) for x in backend.calls[arm*3:arm*3+3]] == [('REQUIRED_SMOKE', 7), ('REQUIRED_SMOKE', 5), ('TARGET_Q32', plan['arm_target_modes'][arm])]
    result = json.loads((base / 'nominal/RECEIPT.json').read_text())
    assert (result['simulated_workers'], result['simulated_BFS'], result['simulated_init_only_cancels']) == (12, 152, 8)
    assert result['actual_GPU_dispatches'] == 0
    assert all(a['required_smoke_envelopes_ns'] > 0 and a['target_CPU_reference_replay_ms'] > 0 and a['algorithm_preparation_CPU_reverse_ms'] > 0 for a in result['arms'])
    assert all(w['existing_child_metrics']['H2D_only_ms'] == 'UNKNOWN' and w['memory']['actual_OS_peak'].startswith('UNKNOWN') for w in result['workers'])
    assert result['fair_no_reverse_Push_cold_baseline'].startswith('ABSENT')
    assert backend.clock.now() > 180 * 1_000_000_000  # virtual gaps; no sleeping
    passed.append('fixed_order_counts_checks_costs_memory_unknowns_and_gaps')
    frozen = digest(base / 'nominal')
    try:
        runner.run()
    except Stop:
        assert len(backend.calls) == 12 and digest(base / 'nominal') == frozen
        passed.append('completed_campaign_cannot_restart')
    bad = copy.deepcopy(plan)
    bad['required_smoke_per_arm'] = bad['required_smoke_per_arm'][:1]
    try:
        Campaign(bad, base / 'invalid_plan', MockBackend())
    except Stop:
        assert not (base / 'invalid_plan').exists()
        passed.append('missing_required_smoke_rejected_before_work')
    cases = [
        ('error', 1, 'SYNTHETIC_ERROR'), ('cancel', 2, 'SYNTHETIC_CANCEL'),
        ('interrupt', 2, 'SYNTHETIC_INTERRUPT'),
        ('mismatch', 2, 'REQUIRED_GUARD_FAILED'), ('missing_cancel', 0, 'CANCEL_CONTRACT'),
        ('device_budget', 2, 'MEMORY_BUDGET_OR_COVERAGE'),
        ('builder_budget', 2, 'MEMORY_BUDGET_OR_COVERAGE'),
        ('host_budget', 2, 'MEMORY_BUDGET_OR_COVERAGE'),
        ('memory_unknown', 2, 'MEMORY_BUDGET_OR_COVERAGE'),
        ('storage_budget', 2, 'RAW_STORAGE_BUDGET'),
        ('sample_budget', 2, 'OBSERVATION_BUDGET'),
        ('watchdog', 2, 'CHILD_WATCHDOG'), ('arm_deadline', 2, 'ARM_DEADLINE'),
        ('campaign_deadline', 2, 'CAMPAIGN_DEADLINE'),
        ('guard', 2, 'REQUIRED_GUARD_FAILED'), ('retirement', 2, 'REQUIRED_GUARD_FAILED'),
        ('wrong_order', 2, 'WORKER_BOUNDARY_ORDER'), ('clock', 2, 'NONMONOTONIC_HOST_CLOCK'),
        ('cleanup', 2, 'SYNTHETIC_CLEANUP_FAILURE')]
    for fault, index, expected in cases:
        backend = MockBackend(fault, index)
        out = base / fault
        campaign = Campaign(plan, out, backend, backend.clock)
        assert campaign.run() == 'STOPPED', fault
        stop = json.loads((out / 'STOP.json').read_text())
        assert expected in stop['reason'], (fault, stop['reason'])
        assert len(backend.calls) == index + 1, fault
        assert stop['actual_GPU_dispatches'] == 0 and stop['resume_allowed'] is False
        assert backend.cleanup_calls[-1]['failed'] is True
        if fault == 'retirement':
            assert stop['cleanup']['owned_context_retirement_confirmed'] is False
        preserved = digest(out)
        try:
            campaign.run()
        except Stop:
            assert len(backend.calls) == index + 1 and digest(out) == preserved
        else:
            raise AssertionError('FAILED_RUN_RESTARTED')
        if index > 0:
            assert (out / '00.response.json').is_file()
        assert (out / 'ledger.jsonl').stat().st_size > 0
        passed.append(fault + '_stops_and_preserves_raw_no_followup')
    sentinel = base / 'existing_original'
    sentinel.mkdir()
    (sentinel / 'original.txt').write_bytes(b'PRESERVE_THIS_RAW_FILE\n')
    before = digest(sentinel)
    try:
        Campaign(plan, sentinel, MockBackend())
    except FileExistsError:
        assert digest(sentinel) == before
        passed.append('existing_directory_refused_without_overwrite')
    else:
        raise AssertionError('RAW_PATH_WAS_REUSED')
    summary = {'status': 'CPU_MOCK_TESTS_PASS', 'test_count': len(passed), 'passed': passed,
        'actual_GPU_queries_or_dispatches': 0, 'actual_BFS_accuracy_or_performance_runs': 0,
        'new_compilations': 0, 'live_GPU_adapter_implemented': False,
        'real_OS_memory_or_watchdog_coverage_validated': False,
        'all_timing_and_memory_values_in_test_receipts': 'SYNTHETIC_NOT_MEASUREMENTS',
        'CPU_mock_cases_failed': 0}
    with (base / 'TEST_RESULTS.json').open('x') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
