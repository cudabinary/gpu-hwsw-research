#!/usr/bin/env python3
"""Independent Python verification of stage 2, including finite proof checks."""
from pathlib import Path
from collections import deque
import json
P=Path(__file__).resolve().parents[1];F=P/'fixtures';R=P/'results'
def bfs(a,s):
 d=[-1]*len(a);d[s]=0;q=deque([s])
 while q:
  u=q.popleft()
  for v in a[u]:
   if d[v]<0:d[v]=d[u]+1;q.append(v)
 return d
adj={};cache={};arrays=elements=0
for line in (R/'guard_arrays.jsonl').open():
 x=json.loads(line);fn=x['file'];n=x['n'];s=x['source']
 if fn not in adj:
  a=[[]for _ in range(n)]
  for line0 in (F/fn).read_text().splitlines():
   if not line0 or line0.startswith(('#','%')):continue
   u,v=map(int,line0.split());a[u].append(v)
  adj[fn]=a
 if (fn,s) not in cache:cache[(fn,s)]=bfs(adj[fn],s)
 assert x['distance']==cache[(fn,s)],(fn,s,x['mode'])
 arrays+=1;elements+=n
tri=frontier_bound=closure=0
for mask in range(512):
 a=[[]for _ in range(3)]
 for i in range(9):
  if mask>>i&1:a[i//3].append(i%3)
 ds=[bfs(a,s)for s in range(3)]
 for r in range(3):
  for s in range(3):
   if ds[r][s]<0:continue
   for v in range(3):
    if ds[s][v]>=0:
     assert ds[r][v]>=0;closure+=1
     assert ds[r][v]<=ds[r][s]+ds[s][v];tri+=1
   for level in range(3):
    front=[u for u in range(3)if ds[s][u]==level]
    if not front:continue
    bound=max(ds[r][u]for u in front)+1
    for u in front:
     for v in a[u]:assert ds[r][v]<=bound;frontier_bound+=1
# Falsification examples: these are deliberately incorrect simplifications.
examples=[]
a=[[1],[2],[]];prefix={0,1};assert 2 not in prefix and 2 in a[1]
examples.append({'invalid_rule':'A partial BFS prefix is a closed region','edges':[[0,1],[1,2]],'prefix':[0,1],'counterexample_edge':[1,2]})
# Outgoing mass of R is not global incoming mass of R.
inside={1,2};out=sum(len(a[v])for v in inside);inc=sum(v in inside for row in a for v in row)
assert out==1 and inc==2
examples.append({'invalid_rule':'regional incoming mass equals outgoing[R] in directed graphs','region':[1,2],'outgoing_mass':out,'incoming_mass':inc})
a=[[]for _ in range(9)]
es=[(0,6),(0,1),(1,2),(2,5),(0,3),(3,4),(4,7),(5,6),(5,7),(7,8)]
for u,v in es:a[u].append(v)
dr,ds=bfs(a,0),bfs(a,5);front=[u for u in range(9)if ds[u]==1]
assert front==[6,7] and dr[8]>min(dr[u]for u in front)+1 and dr[8]<=max(dr[u]for u in front)+1
examples.append({'invalid_rule':'use MIN old frontier distance instead of MAX','edges':es,'old_source':0,'new_source':5,'frontier':front,'wrong_cutoff':min(dr[u]for u in front)+1,'safe_cutoff':max(dr[u]for u in front)+1,'incorrectly_dropped_vertex':8,'old_distances':dr,'new_distances':ds})
# Too far for THIS level must not be declared permanently unreachable.
a=[[1],[2],[3],[]];ds=bfs(a,0);assert ds[3]>1 and ds[3]>=0
examples.append({'invalid_rule':'current-level distance filter implies permanently unreachable','edges':[[0,1],[1,2],[2,3]],'source':0,'level':0,'temporarily_excluded_vertex':3,'true_distance':3})
(R/'COUNTEREXAMPLES.json').write_text(json.dumps(examples,indent=2))
receipt={'status':'PASS','arrays':arrays,'array_elements':elements,'independent_graph_source_oracles':len(cache),'directed_graphs_exhausted':512,'triangle_inequalities':tri,'closure_checks':closure,'frontier_bound_edge_checks':frontier_bound,'negative_rule_counterexamples':len(examples),'GPU':0,'sanitizer':0}
(R/'GUARD_PYTHON_CHECK.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
