"""Reaggregate existing measurements only. Never starts a benchmark."""
from pathlib import Path
import csv,json,collections,statistics,shutil
P=Path(__file__).resolve().parents[1]
def rows(p):return list(csv.DictReader((P/p).open(encoding='utf-8-sig')))
def save(p,data):
    with (P/p).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
by=collections.defaultdict(dict)
for session in range(3):
    for r in rows(f'results/gate_{session}.csv'):
        by[(r['graph'],r['schedule'],r['certificate'],r['mode'])][(r['session'],r['round'])]=float(r['ns'])
work=collections.defaultdict(lambda:[0,0])
for r in rows('results/work.csv'):
    x=work[(r['graph'],r['schedule'],r['mode'])];x[0]+=int(r['edges']);x[1]+=int(r['vertex_tests'])
controls=['OLD_P0','OLD_P2','PUSH_N','DO_N','DO_RIE','PUSH_WCC','LAST_RESULT_REUSE']
out=[]
for (g,s,c,m),v in by.items():
    strongest=min(controls,key=lambda x:statistics.median(by[(g,s,c,x)].values()))
    for baseline in dict.fromkeys(['PUSH_N','DO_N','DO_RIE',strongest]):
        b=by[(g,s,c,baseline)];ratios=[value/b[pair] for pair,value in v.items()]
        out.append(dict(graph=g,schedule=s,certificate=c,mode=m,baseline=baseline,strongest_non_rcc=strongest,median_ns=statistics.median(v.values()),median_paired_ratio=statistics.median(ratios),min_ratio=min(ratios),max_ratio=max(ratios),wins=sum(x<1 for x in ratios),pairs=len(ratios),edge_savings=work[(g,s,baseline)][0]-work[(g,s,m)][0] if c=='cold' else 'UNKNOWN',vertex_test_savings=work[(g,s,baseline)][1]-work[(g,s,m)][1] if c=='cold' else 'UNKNOWN',work_condition='cold_measured' if c=='cold' else 'warm_work_not_measured'))
old=P/'results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv'
if not old.exists():shutil.copyfile(P/'CPU_INCREMENTAL_VALUE.csv',old)
save('CPU_INCREMENTAL_VALUE.csv',out)
lj=next(r for r in out if (r['graph'],r['schedule'],r['certificate'],r['mode'],r['baseline'])==('livejournal_sampled_4096','original','cold','DO_RIE','OLD_P2'))
service=[]
for session in range(3):service+=rows(f'results/service_{session}.csv')
sg=collections.defaultdict(dict)
for r in service:sg[(r['graph'],r['mode'],r['path'],r['q'])][(r['session'],r['round'])]=r
a=[]
for (g,m,path,q),v in sg.items():
    b=sg[(g,'PUSH_N','csr',q)]
    for col in ('a_compute_ns','a_completion_ns'):
        values=[float(r[col])/float(b[pair][col]) for pair,r in v.items()]
        a.append(dict(graph=g,mode=m,path=path,q=q,metric=col,median_paired_ratio=statistics.median(values),min_ratio=min(values),max_ratio=max(values),pairs=len(values)))
save('CPU_PLAN_A_INTERFERENCE.csv',a)
audit=dict(status='LIMITATION_CONFIRMED',consumer_controls=controls,corrected_comparison_rows=len(out),new_benchmark_processes=0,original_P2_is_LJ_resident_winner=True,DO_RIE_over_OLD_P2=lj['median_paired_ratio'],service_original_P0_P2_not_measured=True,reason='Initial service gate enumerated only new modes and omitted the original P2. No remeasurement after the fixed 3-process/7-round budget. Universal strongest end-to-end winner remains UNKNOWN.')
(P/'audit/STRONG_BASELINE_LIMITATION.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
notice=f"""
## Strongest-baseline audit

Original OLD_P2 is a valid non-RCC baseline. With the original LiveJournal input and a resident consumer, OLD_P2 took 0.7263 times as long as PUSH_N. The median paired DO_RIE / OLD_P2 ratio was **{lj['median_paired_ratio']:.4f}**. RIE reduced work relative to DO_N within the same adapter. Runtime also depends on exact discovery counting, termination checks, the bridge's validation and control logic, and code generation. The experiment did not isolate those individual contributions.

The initial service gate omitted OLD_P0 and OLD_P2. The configuration in `config/service_modes.txt` and the original aggregation were preserved. `CPU_INCREMENTAL_VALUE.csv` was regenerated from existing raw data to include these modes in the strongest resident baseline. The initial aggregation is retained in `results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv`. No additional CPU benchmark was run at this checkpoint.

In the measured cold q32 service, Push+RCC_TABLE took 0.7999 times as long as PUSH_N and 0.8999 times as long as sequential DO_RIE. **The strongest full-service path remains unknown at this checkpoint**, pending a comparison with original OLD_P2 under the same owned-output contract. The earlier P2 value of 0.840713 used a different measurement boundary. The minimum follow-up is a paired comparison of frozen P2's sequential and ready paths against Push+RCC_TABLE under the same output contract. It was outside this checkpoint's completed budget of three CPU processes with seven rounds each.

The GPU pilot checked correctness for two candidates and their controls. It passed cancellation, source switching, and full-array comparisons. Graph version mismatch, allocation failure, and dispatch limits were covered through CPU tests or static guards. The pilot did not inject those failures on the GPU or measure the missing CPU baseline.
"""
for name in ('README_FIRST_KO.md','FINAL_DECISION.md','COST_AND_INTERFERENCE_ANALYSIS.md','SOURCE_BASELINE_RECONCILIATION.md'):
    p=P/name;text=p.read_text(encoding='utf-8')
    if '## Strongest-baseline audit' not in text:
        first,rest=text.split('\n',1);p.write_text(first+'\n'+notice+'\n'+rest,encoding='utf-8')
p=P/'REPRODUCE.md';text=p.read_text(encoding='utf-8')
if 'Run the final aggregation audit' not in text:text+='\nRun the final aggregation audit with `python tools/report.py` followed by `python tools/strong_control_audit.py`. The audit reads existing CSV results and runs no benchmarks.\n'
p.write_text(text,encoding='utf-8')
# q-by-q A interference is explicitly separated from service completion.
picked=[r for r in a if r['graph']=='livejournal_sampled_4096' and r['q']=='32' and r['mode'] in ('PUSH_RCC_TABLE','DO_RIE') and r['path'] in ('csr','deferred','concurrent')]
text='\n## Paired interference with A on the original LiveJournal input at q32\n\n| Mode | Path | Metric | Median ratio / PUSH_N service |\n|---|---|---|---|\n'
for r in picked:text+=f"| {r['mode']} | {r['path']} | {r['metric']} | {r['median_paired_ratio']:.4f} |\n"
text+='\nA completion includes advance allocations, thread startup, and certificate publication. The experiment did not resolve small effects or interference of 1% or less.\n'
p=P/'COST_AND_INTERFERENCE_ANALYSIS.md';previous=p.read_text(encoding='utf-8').split('\n## Paired interference with A')[0];p.write_text(previous+text,encoding='utf-8')
summary=json.loads((P/'results/FINAL_SUMMARY.json').read_text(encoding='utf-8'));summary['strong_service_baseline_limit']=audit
(P/'results/FINAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
# Record the paid historical work in the warmed-certificate condition.
hist=collections.defaultdict(list)
for session in range(3):
    for r in rows(f'results/gate_{session}.csv'):
        if r['certificate']=='warm':hist[(r['graph'],r['schedule'],r['mode'])].append(r)
cost=[]
for (g,s,m),v in hist.items():
    cost.append(dict(graph=g,schedule=s,mode=m,prior_requests=3,measured_current_requests=33,median_current_ns=statistics.median(float(r['ns']) for r in v),median_priming_ns=statistics.median(float(r['priming_ns']) for r in v),median_history_plus_current_ns=statistics.median(float(r['ns'])+float(r['priming_ns']) for r in v),classification='CALCULATED_SUM_OF_MEASURED_RESIDENT_COMPONENTS; reverse preparation excluded'))
save('CPU_CERTIFICATE_HISTORY_COST.csv',cost)
print(json.dumps(audit,ensure_ascii=False))
