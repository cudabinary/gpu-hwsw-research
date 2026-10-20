#!/usr/bin/env python3
"""Deterministic local-only input/schedule definition, fixed before timing."""
from pathlib import Path
import random,json,hashlib,platform,subprocess
P=Path(__file__).resolve().parents[1];F=P/'fixtures'
legacy=[]
for line in (F/'cases_original.txt').read_text().splitlines():
 t=line.split();legacy.append((t[0],t[1],int(t[2]),list(map(int,t[3:]))))
# Directed nested domains, all in ONE weakly-connected component.
# Synthetic mechanism witness, NOT a real service trace or held-out discovery.
rng=random.Random(94271021)
for label,nrooms,size,deg in [('oneway_rooms',8,256,24),('oneway_dense',4,256,128)]:
 n=nrooms*size;edges=[]
 for k in range(nrooms):
  for u in range(k*size,(k+1)*size):
   edges.append((u,k*size+(u+1-k*size)%size))
   for _ in range(deg-1):edges.append((u,k*size+rng.randrange(size)))
  if k+1<nrooms:edges.append((k*size,(k+1)*size))
 fn=label+'.edges';(F/fn).write_text(''.join(f'{u} {v}\n' for u,v in edges))
 # Nested phase changes; 33 source requests, no adjacent duplicate.
 seq=[size*(nrooms//2)+(17*i)%size for i in range(33)]
 legacy.append((label,fn,n,seq))
# Counterexample: large unreachable region has dense INCOMING edges into a small
# reachable tail. Closure pruning does not avoid every predecessor source probe.
label='external_incoming';n=2048;edges=[]
for u in range(1536):
 edges.append((u,(u+1)%1536))
 for _ in range(4):edges.append((u,1536+rng.randrange(512)))
for u in range(1536,2048):
 edges.append((u,1536+(u-1536+1)%512))
 for _ in range(7):edges.append((u,1536+rng.randrange(512)))
(F/(label+'.edges')).write_text(''.join(f'{u} {v}\n' for u,v in edges))
legacy.append((label,label+'.edges',n,[1536+(17*i)%512 for i in range(33)]))
unique=[]
for j,(name,fn,n,_) in enumerate(legacy):
 r=random.Random(938201+j);unique.append((name,fn,n,r.sample(range(n),33)))
for sch,cs in [('legacy',legacy),('unique',unique)]:
 (F/f'scope_cases_{sch}.txt').write_text(''.join(f'{a} {b} {n} '+ ' '.join(map(str,ss))+'\n' for a,b,n,ss in cs))
protocol={'module':'RCC-Scope v0.1','cpu_only':True,'gpu_runs':0,'sanitizer_runs':0,
 'timing_sessions':3,'warm_rounds_per_process':7,'warm_q':[8,32],
 'cold_rounds_per_process':3,'cold_q':[32],
 'legacy_sources':'prior already-seen schedules plus deliberately targeted synthetic cases',
 'unique_sources':'seed 938201+case-index, 33 without replacement fixed before timing; not unseen graphs',
 'same_source_reuse':'immediately repeated source uses existing exact output for ALL modes',
 'scope_policy':'alpha=15 beta=24 unchanged; scoped variant replaces n and exact global-indegree sum with domain statistics',
 'output':'full dense distance[n] including -1; per-query copy included, oracle check/file logging outside timed boundary',
 'resident_reverse':'graph/reverse prepared outside timed boundary; workspace+certificate/WCC allocation/updates/destruction inside',
 'cold_reverse':'graph resident; reverse construction when needed + queries inside; input IO and graph parsing outside',
 'memory':'array payload capacities, not RSS/allocator headers or GPU VRAM',
 'negative_controls':['road','google','livejournal','chain','external_incoming'],
 'environment':{'platform':platform.platform(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0]},
 'modes':['PUSH_N','PUSH_RCC_TABLE','DO_RIE','DO_RIE_RCC_TABLE','DO_COMPACT','DO_CLOSURE_COUNT','DO_SCOPE_GLOBAL','DO_SCOPE_LOCAL','DO_SCOPE_COMPACT','DO_WCC_LOCAL','PUSH_WCC']}
protocol['fixture_inputs']=[{'name':a,'n':n,'file':b,'sha256':hashlib.sha256((F/b).read_bytes()).hexdigest(),'type':('prior_derived_real' if a in ('google_sampled_1024','livejournal_sampled_4096','road_sampled_64','lj_permuted') else 'synthetic')}for a,b,n,_ in legacy]
protocol['schedule_hashes']={sch:hashlib.sha256((F/f'scope_cases_{sch}.txt').read_bytes()).hexdigest() for sch in ('legacy','unique')}
(P/'results'/'PROTOCOL_FROZEN.json').write_text(json.dumps(protocol,indent=2))
print(json.dumps({'cases':len(legacy),'schedule_cases':len(legacy)+len(unique),'status':'FROZEN_BEFORE_TIMING'}))
