"""Targeted real-child stop verification after the cleanup accounting change."""
from pathlib import Path
import json, sys

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'src'))
from host_wrapper import Campaign
from owned_child_backend import OwnedChildBackend

R = P / 'results/CPU_ADAPTER_STOP_CHECK'
R.mkdir(parents=True, exist_ok=False)
plan = json.loads((P / 'config/PLAN_CPU_ONLY.json').read_text())
plan['gap_seconds_after_every_completed_arm'] = 0
plan['CPU_protocol_fixture_only'] = True
backend = OwnedChildBackend(R / 'campaign/owned_children', {2: 'cancel'})
runner = Campaign(plan, R / 'campaign', backend, backend.clock)
assert runner.run() == 'STOPPED' and len(backend.calls) == 3
stop = json.loads((R / 'campaign/STOP.json').read_text())
assert 'CPU_PARENT_CANCELLED' in stop['reason'] and not stop['resume_allowed']
assert stop['cleanup']['owned_context_retirement_confirmed']
fake = R / 'unconfirmed'
(fake / '00').mkdir(parents=True)
(fake / '00/TRANSPORT_RECEIPT.json').write_text(json.dumps({'owned_process_exited': False}))
unknown = OwnedChildBackend(fake)
unknown.calls = [{'index': 0}]
assert unknown.cleanup(None, True, lambda *a, **k: None, unknown.clock)['owned_context_retirement_confirmed'] is False
result = {'status': 'CPU_ADAPTER_STOP_CHECK_PASS', 'actual_CPU_fixture_processes': 3,
          'actual_GPU_queries_or_dispatches': 0, 'checks': ['real_cancel_no_fourth_dispatch', 'failed_worker_included_in_cleanup_ledger', 'unconfirmed_own_exit_not_claimed_confirmed']}
(R / 'SUMMARY.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
