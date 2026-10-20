"""Audit/reduce frozen raw data only. Never launches benchmark processes."""
from collections import defaultdict,Counter
import csv
import json
import math
import statistics as stats
from audit_scope_distance import ROOT,PACKAGE,OUT,readcsv,save

protocol=json.loads((ROOT/'research/SCOPE_DISTANCE_PROTOCOL.json').read_text())
assert json.loads((OUT/'BENCHMARK_COMPLETED.json').read_text())['status']=='PASS'
rows=[]
for s in range(3):
    part=readcsv(OUT/f'service_{s}.csv')
    assert len(part)==8960 and all(int(r['session'])==s for r in part)
    rows+=part
assert len(rows)==26880 and sum(int(r['arrays']) for r in rows)==564480
fields=['graph','schedule','q','path']
keyfields=fields+['session','round','sweep','mode']
lookup={};blocks=defaultdict(list);groups=defaultdict(list)
for r in rows:
    key=tuple(r[f] for f in keyfields)
    assert key not in lookup
    lookup[key]=r
    assert r['graph'] in protocol['fixtures'] and r['schedule'] in protocol['schedules'] and int(r['q']) in protocol['q'] and r['path'] in protocol['paths'] and r['mode'] in protocol['modes']
    assert 0<=int(r['round'])<7 and int(r['sweep']) in (0,1)
    assert int(r['arrays'])==int(r['q'])+1
    assert 0<float(r['prepare_ns']) and 0<float(r['queries_ns'])
    assert float(r['prepare_ns'])+float(r['queries_ns'])<=float(r['service_ns'])<=float(r['lifecycle_ns'])
    assert r['path']=='ready' or float(r['historical_prepare_ns'])==0
    blocks[tuple(r[f] for f in fields+['session','round'])].append(r)
    groups[tuple(r[f] for f in fields+['mode'])].append(r)
assert len(blocks)==40*21 and len(groups)==40*16
for block in blocks.values():
    a=sorted([r for r in block if r['sweep']=='0'],key=lambda r:int(r['order_index']))
    b=sorted([r for r in block if r['sweep']=='1'],key=lambda r:int(r['order_index']))
    assert len(a)==len(b)==16 and [r['mode'] for r in a]==[r['mode'] for r in reversed(b)]
    assert {r['mode'] for r in a}==set(protocol['modes'])
costs=[];noise=[]
for key,rr in groups.items():
    assert len(rr)==42
    costs.append(dict(zip(fields+['mode'],key))|{
        'median_'+m:stats.median(float(r[m]) for r in rr)
        for m in ('service_ns','prepare_ns','queries_ns','historical_prepare_ns','validation_ns','release_ns','lifecycle_ns','cache_bytes','payload_upper_bytes')
    })
    g,sch,q,path,mode=key
    ratios=[float(lookup[(g,sch,q,path,str(s),str(b),'1',mode)]['service_ns'])/float(lookup[(g,sch,q,path,str(s),str(b),'0',mode)]['service_ns']) for s in range(3) for b in range(7)]
    noise.append(dict(zip(fields+['mode'],key))|dict(median_ratio=stats.median(ratios),min_ratio=min(ratios),max_ratio=max(ratios),session_medians=[stats.median(ratios[s*7:s*7+7]) for s in range(3)]))
save('COSTS.json',costs);save('NOISE_CONTROLS.json',noise)
candidates=['SCOPE_GLOBAL','SCOPE_LOCAL','SCOPE_COMPACT','DIST_CLOSURE','DIST_RADIUS','DIST_FRONTIER']
controls=['PUSH_N']+protocol['required_controls']
pairs={(c,b) for c in candidates for b in controls}
pairs.update((t.split(' -> ')[1],t.split(' -> ')[0]) for t in protocol['matched_ablations'])
predeclared_pairs=set(pairs)
# Descriptive cross-representation checks do not change the frozen primary gate.
pairs.update(('DIST_FRONTIER',b) for b in ('DIST_COUNT','SCOPE_GLOBAL','SCOPE_LOCAL','SCOPE_COMPACT'))
def value(r,metric):
    if metric=='history_inclusive_ns':return float(r['service_ns'])+float(r['historical_prepare_ns'])
    return float(r[metric])
comparisons=[];comparison_lookup={}
conditions=sorted({tuple(r[f] for f in fields) for r in rows})
for cond in conditions:
    for candidate,baseline in sorted(pairs):
        for metric in ('service_ns','history_inclusive_ns','lifecycle_ns'):
            ratios=[]
            for s in range(3):
                for b in range(7):
                    rr=[value(lookup[(*cond,str(s),str(b),str(w),candidate)],metric)/value(lookup[(*cond,str(s),str(b),str(w),baseline)],metric) for w in range(2)]
                    ratios.append(math.sqrt(rr[0]*rr[1]))
            sessions=[stats.median(ratios[s*7:s*7+7]) for s in range(3)]
            wins=sum(r<1 for r in ratios);median=stats.median(ratios)
            item=dict(zip(fields,cond))|dict(candidate=candidate,baseline=baseline,metric=metric,median_paired_ratio=median,wins=wins,blocks=21,sessions=sessions,min_ratio=min(ratios),max_ratio=max(ratios),guarded_advantage=median<.95 and wins>=17 and all(s<.95 for s in sessions),predeclared_pair=(candidate,baseline) in predeclared_pairs)
            comparisons.append(item);comparison_lookup[(*cond,candidate,baseline,metric)]=item
# CSV is compact and preserves all pair/session/extreme results.
with (OUT/'COMPARISONS.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(comparisons[0]));writer.writeheader()
    writer.writerows([{**r,'sessions':'|'.join(map(str,r['sessions']))} for r in comparisons])
decisions=[]
for cond in conditions:
    for candidate in candidates:
        baseline='SCOPE_COUNT' if candidate=='SCOPE_GLOBAL' else 'SCOPE_GLOBAL' if candidate=='SCOPE_LOCAL' else 'SCOPE_LOCAL' if candidate=='SCOPE_COMPACT' else 'DIST_COUNT' if candidate=='DIST_CLOSURE' else 'DIST_CLOSURE' if candidate=='DIST_RADIUS' else 'DIST_RADIUS'
        for metric in ('service_ns','history_inclusive_ns'):
            cc=[comparison_lookup[(*cond,candidate,b,metric)] for b in controls]
            matched=comparison_lookup[(*cond,candidate,baseline,metric)]
            decisions.append(dict(zip(fields,cond))|dict(candidate=candidate,metric=metric,beats_all_fixed_controls=all(r['guarded_advantage'] for r in cc),matched_ablation=baseline,matched_ablation_gate=matched['guarded_advantage'],all_gates=all(r['guarded_advantage'] for r in cc) and matched['guarded_advantage'],failed_controls=[r['baseline'] for r in cc if not r['guarded_advantage']],worst_control_ratio=max(r['median_paired_ratio'] for r in cc)))
save('DECISIONS.json',decisions)
# Mechanism measurements replay the original matched pruning rules exactly.
work=readcsv(OUT/'matched/work.csv');workgroups=defaultdict(Counter)
for r in work:
    group=workgroups[(r['graph'],r['schedule'],r['mode'])]
    for k in ('edges','vertex_tests','levels','publish_tests','publish_writes','closure_skips','future_skips','old_distance_reads','reused'):group[k]+=int(r[k])
    group['max_cache_bytes']=max(group['max_cache_bytes'],int(r['cache_bytes']))
workrows=[dict(graph=k[0],schedule=k[1],mode=k[2],**v) for k,v in sorted(workgroups.items())]
save('WORK_SUMMARY.json',workrows)
ledger=[]
for graph,sch in sorted({k[:2] for k in workgroups}):
    for candidate,base in [('SCOPE_GLOBAL','SCOPE_COUNT'),('DIST_CLOSURE','DIST_COUNT'),('DIST_RADIUS','DIST_CLOSURE'),('DIST_FRONTIER','DIST_RADIUS'),('DIST_FRONTIER','DIST_COUNT'),('DIST_FRONTIER','DO_RIE'),('DIST_FRONTIER','DO_RIE_RCC_TABLE')]:
        a=workgroups[(graph,sch,candidate)];b=workgroups[(graph,sch,base)]
        ledger.append(dict(graph=graph,schedule=sch,candidate=candidate,baseline=base,baseline_edges=b['edges'],candidate_edges=a['edges'],saved_edges=b['edges']-a['edges'],saved_vertex_tests=b['vertex_tests']-a['vertex_tests'],added_old_distance_reads=a['old_distance_reads']-b['old_distance_reads'],same_levels=a['levels']==b['levels'],not_DRAM_bytes=True))
save('MECHANISM_LEDGER.json',ledger)
# Recompute supplied timing summaries, without replaying its benchmark commands.
guard=[]
for s in range(3):guard+=readcsv(PACKAGE/f'results/guard_timing_s{s}.csv')
assert len(guard)==4032
glookup={(r['graph'],r['schedule'],r['session'],r['round'],r['mode']):r for r in guard}
assert len(glookup)==len(guard)
historical_pairs=readcsv(PACKAGE/'results/GUARD_PAIRED.csv')
for item in historical_pairs:
    ratios=[float(glookup[(item['graph'],item['schedule'],str(s),str(b),item['baseline'])]['elapsed_ns'])/float(glookup[(item['graph'],item['schedule'],str(s),str(b),item['candidate'])]['elapsed_ns']) for s in range(3) for b in range(7)]
    assert math.isclose(stats.median(ratios),float(item['median_speedup']),rel_tol=1e-10)
    assert sum(x>1 for x in ratios)==int(item['pair_wins'])
scope_rows=[]
for boundary in ('resident','cold'):
    for s in range(3):scope_rows += [(boundary,r) for r in readcsv(PACKAGE/f'results/timing_{boundary}_s{s}.csv')]
assert len(scope_rows)==13464
historical_groups=defaultdict(list)
for boundary,r in scope_rows:historical_groups[(boundary,r['graph'],r['schedule'],r['q'],r['mode'])].append(float(r['elapsed_ns']))
timings=readcsv(PACKAGE/'results/TIMING_SUMMARY.csv')
for item in timings:
    rr=historical_groups[(item['boundary'],item['graph'],item['schedule'],item['q'],item['mode'])]
    assert len(rr)==int(item['n']) and math.isclose(stats.median(rr)/1e6,float(item['median_ms']),rel_tol=1e-10)
save('HISTORICAL_REANALYSIS.json',dict(status='PASS',guard_raw_rows=len(guard),guard_paired_summaries_verified=len(historical_pairs),scope_raw_rows=len(scope_rows),scope_timing_summaries_verified=len(timings),historical_timings_not_pooled_with_local=True,provided_posthoc_best_baseline_not_an_online_policy=True))
save('ANALYSIS.json',dict(status='PASS',timing_rows=len(rows),full_array_checks=564480,conditions=len(conditions),modes=16,blocks_per_condition=21,sessions=3,comparison_rows=len(comparisons),exact_mirror_order=True,no_outliers_removed=True,new_GPU_runs=0,default_RCC_integrated=False,candidate_API_compatibility='NOT_IMPLEMENTED_NOT_VERIFIED',existing_API_compatibility='PASS',strict_scope_transient_memory_upper_bound=False,notes='payload_upper_bytes omits transient old+new closure publication and allocator metadata; RSS separately measured. New service starts first policy query from cold history, not historical external fixed A.'))
print(json.dumps(dict(status='ANALYSIS_PASS',trials=len(rows),all_gates_passed=[r for r in decisions if r['all_gates']]),indent=2))
