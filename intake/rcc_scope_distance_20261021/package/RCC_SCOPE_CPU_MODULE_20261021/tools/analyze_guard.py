#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
P=Path(__file__).resolve().parents[1];r=P/'results'
w=pd.read_csv(r/'guard_work.csv')
s=w.groupby(['graph','schedule','mode'])[['edges','vertex_tests','levels','closure_skips','future_skips','old_distance_reads']].sum()
s.to_csv(r/'GUARD_WORK_SUMMARY.csv')
d=pd.concat([pd.read_csv(f)for f in sorted(r.glob('guard_timing_s*.csv'))])
assert not d.duplicated(['graph','schedule','session','round','mode']).any()
med=d.groupby(['graph','schedule','mode']).elapsed_ns.median().div(1e6).rename('median_ms').reset_index();med.to_csv(r/'GUARD_TIMING_SUMMARY.csv',index=False)
rows=[]
for key,x in d.groupby(['graph','schedule']):
 t=x.pivot(index=['session','round'],columns='mode',values='elapsed_ns')
 for b,c in [('LAST_COUNT','LAST_CLOSURE'),('LAST_CLOSURE','LAST_RADIUS'),('LAST_RADIUS','LAST_FRONTIER'),('DO_RIE','LAST_FRONTIER'),('PUSH_RCC_TABLE','LAST_FRONTIER')]:
  q=t[b]/t[c];ss=q.groupby('session').median()
  rows.append(dict(graph=key[0],schedule=key[1],baseline=b,candidate=c,median_speedup=q.median(),min_speedup=q.min(),max_speedup=q.max(),pair_wins=int((q>1).sum()),pairs=len(q),session_wins=int((ss>1).sum()),session_medians='|'.join(map(str,ss.values))))
pd.DataFrame(rows).to_csv(r/'GUARD_PAIRED.csv',index=False)
rows=[]
for graph,sch in sorted({(i[0],i[1])for i in s.index}):
 b=s.loc[(graph,sch,'DO_RIE')];x=s.loc[(graph,sch,'LAST_FRONTIER')]
 rows.append(dict(graph=graph,schedule=sch,original_edge_probes=int(b.edges),new_edge_probes=int(x.edges),saved_edge_probes=int(b.edges-x.edges),saved_probes_pct=100*(b.edges-x.edges)/b.edges if b.edges else 0,additional_prior_distance_reads=int(x.old_distance_reads),logical_avoided_neighbor_bytes=4*int(b.edges-x.edges),logical_prior_distance_read_bytes=4*int(x.old_distance_reads),not_DRAM_bytes=True))
pd.DataFrame(rows).to_csv(r/'GUARD_LOGICAL_READ_LEDGER.csv',index=False)
print('PASS: guard raw timings/work recomputed; no new benchmark run')
