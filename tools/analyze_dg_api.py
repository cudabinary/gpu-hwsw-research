"""Analyze the fixed campaign without dropping outliers or pooling earlier runs."""
from pathlib import Path
from collections import defaultdict
import csv,json,statistics as st,random,itertools,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/dg_api_20261021'
def save(name,v):(OUT/name).write_text(json.dumps(v,indent=2)+'\n')
def read(name):
    with (OUT/name).open() as f:return list(csv.DictReader(f))
def percentile(x,p):
    x=sorted(x);at=(len(x)-1)*p;lo=int(at);return x[lo]+(x[min(lo+1,len(x)-1)]-x[lo])*(at-lo)
def summarize(x):return dict(median=st.median(x),minimum=min(x),maximum=max(x),p05=percentile(x,.05),p95=percentile(x,.95))
def main():
    assert json.loads((OUT/'BENCHMARK_COMPLETED.json').read_text())['status']=='PASS'
    rows=sum([read(f'service_{i}.csv') for i in range(5)],[]);assert len(rows)==26880
    assert sum(int(r['arrays']) for r in rows)==564480
    groups=defaultdict(list);lookup={}
    for r in rows:
        key=tuple(r[k] for k in ('graph','schedule','q','path'));groups[key].append(r)
        rk=key+tuple(int(r[k]) for k in ('session','round','sweep'))+(r['mode'],);assert rk not in lookup;lookup[rk]=r
    rng=random.Random(20261021);samples=[tuple(sorted(rng.randrange(5) for _ in range(5))) for _ in range(10000)];unique=set(samples)
    modes=json.loads((ROOT/'research/DG_API_PROTOCOL.json').read_text())['modes'];pairs=[];costs=[];noise=[]
    strong=['TABLE_DEPLOYED','LAST_DEPLOYED','TABLE_MATCHED','LAST_MATCHED','OLD_P2','RIE','RIE_TABLE','EXACT_REUSE','DG_COUNT','DG_RADIUS']
    for key,rs in sorted(groups.items()):
        context=dict(zip(('graph','schedule','q','path'),key))
        for metric in ('service_ns','history_inclusive_ns'):
            def value(r):return float(r['service_ns'])+(float(r['historical_prepare_ns']) if metric=='history_inclusive_ns' else 0)
            for baseline in modes:
                if baseline=='DG_FRONTIER':continue
                bysession=[];ratios=[]
                for session in range(5):
                    this=[]
                    for round in range(8):
                        candidate=sum(value(lookup[key+(session,round,sweep,'DG_FRONTIER')]) for sweep in range(2))/2
                        reference=sum(value(lookup[key+(session,round,sweep,baseline)]) for sweep in range(2))/2
                        this.append(candidate/reference)
                    bysession.append(this);ratios+=this
                medians=[st.median(x) for x in bysession]
                boots={sample:st.median(list(itertools.chain.from_iterable(bysession[i] for i in sample))) for sample in unique}
                distribution=[boots[s] for s in samples];wins=sum(v<1 for v in ratios)
                pairs.append(dict(**context,metric=metric,candidate='DG_FRONTIER',baseline=baseline,paired_ratios=ratios,ratio_median=st.median(ratios),ratio_min=min(ratios),ratio_max=max(ratios),session_medians=medians,session_range=[min(medians),max(medians)],wins=wins,pairs=40,cluster_bootstrap95=[percentile(distribution,.025),percentile(distribution,.975)],gate=st.median(ratios)<.95 and wins>=32 and all(x<.95 for x in medians)))
        for mode in modes:
            mr=[r for r in rs if r['mode']==mode]
            fields=['service_ns','prepare_ns','queries_ns','historical_prepare_ns','release_ns','module_release_ns','validation_ns','lifecycle_ns','cache_bytes','adapter_csr_bytes','copy_elements','certificates','fallbacks']
            costs.append(dict(**context,mode=mode,measurements={f:summarize([float(r[f]) for r in mr]) for f in fields},history_inclusive_ns=summarize([float(r['service_ns'])+float(r['historical_prepare_ns']) for r in mr])))
            null=[]
            for session in range(5):
                for round in range(8):null.append(float(lookup[key+(session,round,1,mode)]['service_ns'])/float(lookup[key+(session,round,0,mode)]['service_ns']))
            noise.append(dict(**context,mode=mode,mirror_ratio=summarize(null)))
    gates=[]
    for key in sorted(groups):
        for metric in ('service_ns','history_inclusive_ns'):
            selected=[p for p in pairs if tuple(p[k] for k in ('graph','schedule','q','path'))==key and p['metric']==metric and p['baseline'] in strong]
            assert len(selected)==len(strong)
            gates.append(dict(**dict(zip(('graph','schedule','q','path'),key)),metric=metric,gate=all(p['gate'] for p in selected),failed_baselines=[p['baseline'] for p in selected if not p['gate']]))
    phasegroups=defaultdict(list)
    for r in read('phases.csv'):
        if r['mode'].endswith('_DEPLOYED'):continue
        phasegroups[tuple(r[k] for k in ('graph','schedule','q','path','mode'))].append(r)
    phases=[]
    for key,rs in sorted(phasegroups.items()):
        entries=[]
        for r in rs:
            algorithm=float(r['algorithm_ns']);allocation=float(r['allocation_ns']);copy=float(r['copy_ns']);maintenance=float(r['maintenance_ns']);reverse=float(r['lazy_reverse_ns']);internal=float(r['internal_run_ns'])
            # Same diagnostic trial only; includes timer overhead and dispatch.
            residual=internal-algorithm-allocation-copy-maintenance-reverse
            entries.append(dict(algorithm_ns=algorithm,allocation_ns=allocation,copy_ns=copy,maintenance_ns=maintenance,lazy_reverse_ns=reverse,internal_run_ns=internal,internal_residual_ns=residual,service_ns=float(r['service_ns']),prepare_ns=float(r['prepare_ns']),prepare_graph_ns=float(r['prepare_graph_ns']),prepare_reverse_ns=float(r['prepare_reverse_ns']),prepare_workspace_ns=float(r['prepare_workspace_ns']),module_release_ns=float(r['module_release_ns']),consumer_release_ns=float(r['release_ns']),old_reads=float(r['old_reads']),future_skips=float(r['future_skips']),outside_skips=float(r['outside_skips'])))
        phases.append(dict(**dict(zip(('graph','schedule','q','path','mode'),key)),samples=len(rs),median={k:st.median(e[k] for e in entries) for k in entries[0]},intrusive=True,not_primary_timing=True))
    works=defaultdict(lambda:defaultdict(int))
    for r in read('work.csv'):
        key=tuple(r[k] for k in ('graph','schedule','path','mode'))
        for f in ('can_apply','certificate_applied','fallback','edges','old_reads','future_skips','outside_skips'):works[key][f]+=int(r[f])
    mechanism=[dict(**dict(zip(('graph','schedule','path','mode'),k)),**v,edge_counter_available=k[-1]!='OLD_P2') for k,v in sorted(works.items())]
    save('PAIR_STATS.json',pairs);save('COSTS.json',costs);save('NOISE.json',noise);save('PHASE_COSTS.json',phases);save('MECHANISM.json',mechanism);save('GATES.json',gates)
    positives=[g for g in gates if g['gate']]
    summary=dict(status='PASS',trials=len(rows),arrays=564480,mirrored_pairs_per_comparison=40,sessions=5,gate_positive_conditions=positives,verdict='HOLD' if not positives else 'CONDITIONAL_EXPERIMENT_ONLY',no_default_integration=True,limitations=['Five local sequential sessions are not across-day replication.','Bootstrap interval is descriptive, with only five session clusters and no multiple-comparison correction.','Synthetic and derived sampled graphs do not establish population generality.','Counter-enabled CPU API result, not GPU evidence.','Phase clocks are intrusive and separate from the primary campaign.','P2/RIE wrappers are algorithm comparison controls, not certificate-providing integration candidates.','API useful-bound < n semantics exclude all-n previous closures.','Dlopen and API Graph construction are startup costs outside the batch; actual output destruction is included.'])
    summary['default_integration']='HOLD'
    summary['optimization_iterations_after_campaign']=0
    save('ANALYSIS.json',summary)
    # Compact review table, retaining the complete statistics in JSON.
    lines=['# DistanceGuard API fixed campaign','',f'Verdict: **{summary["verdict"]}**. 26,880 trials / 564,480 full arrays; 5 sessions x 8 mirrored rounds.','', 'Ratios: DG_FRONTIER / baseline, ready q32. Each cell is paired median [session-cluster bootstrap 95% interval].','', '| graph / schedule | TABLE deployed | TABLE matched | OLD_P2 | RIE | DG_COUNT | DG_RADIUS |','|---|---:|---:|---:|---:|---:|---:|']
    for key in sorted(groups):
        if key[2:]!=('32','ready'):continue
        cells=[]
        for b in ('TABLE_DEPLOYED','TABLE_MATCHED','OLD_P2','RIE','DG_COUNT','DG_RADIUS'):
            p=next(p for p in pairs if tuple(p[k] for k in ('graph','schedule','q','path'))==key and p['metric']=='service_ns' and p['baseline']==b)
            cells.append(f'{p["ratio_median"]:.4f} [{p["cluster_bootstrap95"][0]:.4f}, {p["cluster_bootstrap95"][1]:.4f}]')
        lines.append('| '+key[0]+' / '+key[1]+' | '+' | '.join(cells)+' |')
    (OUT/'SUMMARY.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
