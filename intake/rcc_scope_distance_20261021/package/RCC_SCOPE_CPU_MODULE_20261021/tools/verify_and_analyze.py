#!/usr/bin/env python3
from pathlib import Path
from collections import deque
import json,csv,gzip,statistics,hashlib,platform
import pandas as pd
P=Path(__file__).resolve().parents[1];R=P/'results';F=P/'fixtures'
# Independent raw-edge-list BFS, no C++ CSR/reverse or certificate code reused.
adj={};oracle={};arrays=vertices=0
with (R/'arrays.jsonl').open() as f:
 for line in f:
  x=json.loads(line);fn=x['file'];n=x['n'];s=x['source']
  if fn not in adj:
   a=[[]for _ in range(n)]
   for line0 in (F/fn).read_text().splitlines():
    if not line0 or line0.startswith(('#','%')):continue
    u,v=map(int,line0.split());assert 0<=u<n and 0<=v<n;a[u].append(v)
   adj[fn]=a
  key=(fn,s)
  if key not in oracle:
   d=[-1]*n;d[s]=0;q=deque([s])
   while q:
    u=q.popleft()
    for v in adj[fn][u]:
     if d[v]<0:d[v]=d[u]+1;q.append(v)
   oracle[key]=d
  assert x['distance']==oracle[key],(fn,s,x['mode'])
  arrays+=1;vertices+=n
receipt={'status':'PASS','arrays':arrays,'array_elements':vertices,'independent_graph_source_oracles':len(oracle),'graph_files':len(adj),'implementation':'Python deque and supplied raw .edges files','gpu_runs':0}
(R/'PYTHON_ARRAY_CHECK.json').write_text(json.dumps(receipt,indent=2))
# Diagnostics are separate from timers.
w=pd.read_csv(R/'work.csv');groups=['graph','schedule','mode']
cols=['edges','vertex_tests','levels','bitmap_clear','publish_tests','publish_writes']
s=w.groupby(groups)[cols].sum().reset_index()
s=s.merge(w.groupby(groups).agg(scope_hits=('hit','sum'),max_extra_bytes=('extra_bytes','max'),min_domain=('domain','min'),max_domain=('domain','max'),same_source_reuse=('stop_reason',lambda t:sum(t==5))).reset_index(),on=groups)
s.to_csv(R/'WORK_SUMMARY.csv',index=False)
base_modes=['PUSH_N','PUSH_RCC_TABLE','DO_RIE','DO_RIE_RCC_TABLE','DO_COMPACT','DO_WCC_LOCAL','PUSH_WCC']
all_summary=[];ratios=[]
for name,glob in [('resident','timing_resident_s*.csv'),('cold','timing_cold_s*.csv')]:
 df=pd.concat([pd.read_csv(x)for x in sorted(R.glob(glob))],ignore_index=True)
 assert not df.duplicated(['graph','schedule','session','round','q','mode']).any()
 for key,ds in df.groupby(['graph','schedule','q']):
  med=ds.groupby('mode').elapsed_ns.median();best=med.loc[base_modes].idxmin()
  for mode,dm in ds.groupby('mode'):
   all_summary.append({'boundary':name,'graph':key[0],'schedule':key[1],'q':key[2],'mode':mode,'median_ms':dm.elapsed_ns.median()/1e6,'min_ms':dm.elapsed_ns.min()/1e6,'max_ms':dm.elapsed_ns.max()/1e6,'n':len(dm),'extra_bytes_max':dm.extra_bytes.max(),'workspace_bytes':dm.workspace_bytes.max(),'best_measured_non_scope':best,'ratio_to_best_medians':med[mode]/med[best]})
  pivot=ds.pivot(index=['session','round'],columns='mode',values='elapsed_ns')
  comparisons=[('DO_CLOSURE_COUNT','DO_SCOPE_GLOBAL'),('DO_RIE','DO_SCOPE_LOCAL'),('DO_COMPACT','DO_SCOPE_COMPACT'),('DO_SCOPE_LOCAL','DO_SCOPE_COMPACT'),(best,'DO_SCOPE_GLOBAL'),(best,'DO_SCOPE_LOCAL'),(best,'DO_SCOPE_COMPACT')]
  for bm,cm in dict.fromkeys(comparisons):
   rr=pivot[bm]/pivot[cm];sr=rr.groupby('session').median()
   ratios.append({'boundary':name,'graph':key[0],'schedule':key[1],'q':key[2],'baseline':bm,'candidate':cm,'paired_speedup_median':rr.median(),'paired_speedup_min':rr.min(),'paired_speedup_max':rr.max(),'pair_wins':int(sum(rr>1)),'pairs':len(rr),'session_wins':int(sum(sr>1)),'sessions':len(sr),'sessions_median_ratios':'|'.join(f'{x:.6f}'for x in sr),'strong_comparator_is_posthoc_descriptive':bm==best})
 pd.DataFrame(all_summary).to_csv(R/'TIMING_SUMMARY.csv',index=False)
 pd.DataFrame(ratios).to_csv(R/'PAIRED_COMPARISONS.csv',index=False)
print(json.dumps(receipt))
print('timing rows',sum(1 for name in R.glob('timing_*.csv') for _ in name.open())-6)
