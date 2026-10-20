"""Read-only audit of fixed CPU trial coverage, timing boundaries and receipts."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import statistics
from run_old_p2_service import ROOT, OUT, pins, protected_snapshot, vendor_check, save

protocol=json.loads((ROOT/'research/OLD_P2_PROTOCOL.json').read_text())
assert json.loads((OUT/'PINS.json').read_text())==pins()
assert protected_snapshot()==json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
rows=[]
for session in range(3):
    with (OUT/f'service_{session}.csv').open() as f:
        current=list(csv.DictReader(f))
    assert len(current)==protocol['trials_per_process']
    assert all(int(r['session'])==session for r in current)
    rows+=current
assert len(rows)==protocol['total_trials']
assert sum(int(r['arrays']) for r in rows)==protocol['total_full_arrays']
keys=collections.Counter(tuple(r[k] for k in ('session','round','sweep','graph','q','mode','path')) for r in rows)
assert len(keys)==len(rows) and set(keys.values())=={1}
blocks=collections.defaultdict(list)
for r in rows:
    q=int(r['q']);assert q in protocol['q'] and int(r['arrays'])==q+1
    assert r['graph'] in protocol['fixtures']
    assert r['mode']+'/'+r['path'] in protocol['variants']
    assert 0<=int(r['round'])<7 and int(r['sweep']) in (0,1)
    assert 0<float(r['a_compute_ns'])<=float(r['a_completion_ns'])<=float(r['total_ns'])
    assert float(r['total_ns'])<=float(r['cleanup_window_ns'])<=float(r['lifecycle_ns'])
    assert 0<int(r['payload_upper_bytes'])<=32*1024*1024
    if r['path']=='ready':
        assert 0<float(r['historical_prepare_ns'])<float(r['lifecycle_ns'])
    else:
        assert float(r['historical_prepare_ns'])==0
    if r['mode']=='OLD_P2':
        assert float(r['a_completion_ns'])<=float(r['b_ready_ns'])<=float(r['total_ns'])
    else:
        assert float(r['b_ready_ns'])==0
    blocks[tuple(r[k] for k in ('session','round','graph','q'))].append(r)
assert len(blocks)==84
for block in blocks.values():
    first=sorted((r for r in block if r['sweep']=='0'),key=lambda r:int(r['order_index']))
    second=sorted((r for r in block if r['sweep']=='1'),key=lambda r:int(r['order_index']))
    assert len(first)==len(second)==4
    assert [(r['mode'],r['path']) for r in first]==[(r['mode'],r['path']) for r in reversed(second)]
costs=[]
for graph in protocol['fixtures']:
    for q in protocol['q']:
        for variant in protocol['variants']:
            selected=[r for r in rows if r['graph']==graph and int(r['q'])==q and r['mode']+'/'+r['path']==variant]
            assert len(selected)==42
            costs.append(dict(graph=graph,q=q,variant=variant,**{
                'median_'+k:statistics.median(float(r[k]) for r in selected)
                for k in ('total_ns','a_compute_ns','a_completion_ns','historical_prepare_ns','validation_ns','release_ns','cleanup_window_ns','lifecycle_ns','payload_upper_bytes')
            }))
save('COSTS.json',costs)
before=json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
save('AUDIT.json',dict(status='PASS',raw_trials=len(rows),complete_mirrored_blocks=len(blocks),full_arrays=14112,distance_elements=14112*4096,all_timing_boundaries_valid=True,complete_fixed_matrix=True,exact_mirror_orders=True,source_binary_protocol_pins_unchanged=True,vendor_files=vendor_check(),original_matching_files=len(before['original_matching_files_sha256']),main_tracked_files=len(before['main_tracked_sha256']),protected_snapshots_equal=True,benchmark_reruns=0,gpu_runs=0,audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
print(json.dumps(json.loads((OUT/'AUDIT.json').read_text()),indent=2))
