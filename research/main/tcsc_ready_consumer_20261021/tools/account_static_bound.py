"""Algebraic counterfactual from saved level accounting; no BFS execution."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'analysis/consumer_attribution_20261021'
O=D/'static_bound';O.mkdir(exist_ok=False)
raw=list(csv.DictReader((D/'level_work.csv').open()))
queries=list(csv.DictReader((D/'query_work.csv').open()))
result=[];facts=[];equivalence_checks=0
for fixture,n in [('livejournal_sampled_4096.edges',4096),('google_sampled_1024.edges',1024)]:
    indegree=[0]*n
    for line in (R/'fixtures'/fixture).read_text().splitlines():
        if line and line[0] not in '#%':indegree[int(line.split()[1])]+=1
    active=sum(x>0 for x in indegree)
    for query in range(32):
        source=17*query;bound=active+int(indegree[source]==0)
        rows=[x for x in raw if x['fixture']==fixture and int(x['mode'])==6 and int(x['query'])==query]
        for x in rows:
            assert (int(x['remaining_in'])==0)==(int(x['seen'])==bound)
            equivalence_checks+=1
        for zero in [False,True]:
            selected=[];reason='FRONTIER_EMPTY_OR_EARLY_N'
            for x in rows:
                if zero and int(x['frontier_edges'])==0:reason='FRONTIER_ZERO';break
                if int(x['seen'])==bound:reason='STATIC_POSITIVE_INDEGREE_BOUND';break
                selected.append(x)
            refmode=5 if zero else 3
            ref=next(x for x in queries if x['fixture']==fixture and int(x['query'])==query and int(x['mode'])==refmode)
            assert len(selected)==int(ref['processed_levels'])
            discoveries=sum(int(x['found']) for x in selected)
            result.append({'fixture':fixture,'query':query,'source':source,
             'control':'Push_bound_zero_stats' if zero else 'Push_bound_lean',
             'static_bound':bound,'same_stop_level_as_existing_mode':refmode,
             'processed_levels':len(selected),'logical_edge_tests':sum(int(x['frontier_edges']) for x in selected),
             'total_kernel_launches':1+len(selected),'policy_degree_atomics':2*discoveries if zero else 0,
             'control_D2H_bytes':28*len(selected),'stop_reason':reason,
             'implementation_status':'HYPOTHETICAL_HOST_CONTROL_NOT_IMPLEMENTED_OR_GPU_TESTED'})
    facts.append({'fixture':fixture,'n':n,'positive_indegree_vertices':active,'zero_indegree_vertices':n-active,
       'static_scan_cost':'n comparisons of reverse row offsets once; source zero-indegree test once per query',
       'extra_persistent_state':'one graph-versioned scalar K; no per-vertex bound table',
       'without_ready_reverse':'Not free: derive nonzero indegree from CSR or existing COUNT metadata; charge construction and storage'})
with (O/'query_controls.csv').open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
summary=[]
for fixture in [x['fixture'] for x in facts]:
 for q in [1,2,8,32]:
  for control in ['Push_bound_lean','Push_bound_zero_stats']:
   rows=[x for x in result if x['fixture']==fixture and x['query']<q and x['control']==control]
   summary.append({'fixture':fixture,'q_prefix':q,'control':control,**{k:sum(x[k] for x in rows) for k in ['processed_levels','logical_edge_tests','total_kernel_launches','policy_degree_atomics','control_D2H_bytes']}})
with (O/'prefix_controls.csv').open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
receipt={'scope':'STATIC_IDENTITY_AND_SAVED_TRACE_ACCOUNTING_ONLY','facts':facts,
 'identity':'remaining_in == 0 iff seen == K + [indegree(source)==0], for valid BFS on immutable directed CSR',
 'reason':'Every reached vertex other than the source has positive indegree; remaining_in is a sum of nonnegative indegrees over unreached vertices.',
 'observed_processed_boundaries_checked':equivalence_checks,'projected_controls':128,
 'current_owner_or_CUDA_changes':0,'GPU_calls':0,'BFS_correctness_suite_runs':0,
 'new_GPU_times':'UNKNOWN','novelty_claim':'NONE; elementary static counting bound, not a new candidate',
 'input_level_work_sha256':hashlib.sha256((D/'level_work.csv').read_bytes()).hexdigest()}
(O/'STATIC_BOUND_IDENTITY.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'facts':facts,'q32':[x for x in summary if x['q_prefix']==32]},indent=2))
