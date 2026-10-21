"""Bounded offline operation accounting, not timing or correctness re-execution.

One frontier partition per fixed source, then symbolic accounting for existing
owner modes. Does not run the owner, compiler, driver, or earlier 402-case suite.
"""
from pathlib import Path
from collections import deque,Counter
import csv,hashlib,json,math
R=Path(__file__).resolve().parents[1]
OUT=R/'analysis/consumer_attribution_20261021'
MODES=[0,2,3,4,5,6]
SOURCES=[17*i for i in range(32)]
def sha(data):return hashlib.sha256(data).hexdigest()
def write_csv(path,rows):
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    pins=json.loads((R/'config/SOURCE_BINARY_INPUT_PINS.json').read_text())['pins']
    for rel,digest in pins.items():
        if sha((R/rel).read_bytes())!=digest:raise RuntimeError('FROZEN_PIN_CHANGED_'+rel)
    queries=[];levels=[];summary=[]
    for fixture,n in [('livejournal_sampled_4096.edges',4096),('google_sampled_1024.edges',1024)]:
        f=R/'fixtures'/fixture;raw=f.read_bytes();adj=[[] for _ in range(n)]
        for line in raw.decode().splitlines():
            if not line or line[0] in '#%':continue
            u,v=map(int,line.split());adj[u].append(v)
        # Mirrors the frozen source-ordered scatter solely to count adjacency
        # tests. This is not a new builder implementation or publication path.
        incoming=[[] for _ in range(n)]
        for u,row in enumerate(adj):
            for v in row:incoming[v].append(u)
        m=sum(map(len,adj));outdeg=list(map(len,adj));indeg=list(map(len,incoming))
        for query,source in enumerate(SOURCES):
            distance=[-1]*n;distance[source]=0;fifo=deque([source])
            while fifo:
                u=fifo.popleft()
                for v in adj[u]:
                    if distance[v]<0:distance[v]=distance[u]+1;fifo.append(v)
            frontier=[[] for _ in range(max(distance)+1)]
            for v,d in enumerate(distance):
                if d>=0:frontier[d].append(v)
            remaining=m;seen=0;base=[]
            for lev,front in enumerate(frontier):
                seen+=len(front);remaining-=sum(indeg[u] for u in front)
                fe=sum(outdeg[u] for u in front)
                unvisited=[v for v,d in enumerate(distance) if d<0 or d>lev]
                pull_tests=0
                for v in unvisited:
                    for u in incoming[v]:
                        pull_tests+=1
                        if distance[u]==lev:break
                found=len(frontier[lev+1]) if lev+1<len(frontier) else 0
                base.append({'level':lev,'frontier':len(front),'frontier_edges':fe,'remaining_in':remaining,
                    'seen':seen,'found':found,'unvisited':len(unvisited),'pull_tests':pull_tests})
            for mode in MODES:
                total=Counter();pull=False;reason=0;stop_level=len(frontier)
                for b in base:
                    if b['seen']==n:reason=1;stop_level=b['level'];break
                    if mode in (4,5) and b['frontier_edges']==0:reason=4;stop_level=b['level'];break
                    if mode in (3,5) and b['remaining_in']==0:reason=2;stop_level=b['level'];break
                    if mode>=2 and mode!=6:
                        if pull:
                            if b['frontier']<max(1,n//24):pull=False
                        elif b['frontier_edges']>b['remaining_in']//15:pull=True
                    stats=mode>=2
                    row={'fixture':fixture,'query':query,'source':source,'mode':mode,**b,
                      'path':'pull' if pull else 'push',
                      'csr_edge_tests':0 if pull else b['frontier_edges'],
                      'reverse_edge_tests':b['pull_tests'] if pull else 0,
                      'push_rows':0 if pull else b['frontier'],
                      'pull_distance_atomic_probes':n if pull else 0,
                      'pull_unvisited_rows':b['unvisited'] if pull else 0,
                      'bitmap_words_zeroed':math.ceil(n/64) if pull else 0,
                      'bitmap_atomic_or':b['frontier'] if pull else 0,
                      'distance_atomic_CAS_attempts':b['found'] if pull else b['frontier_edges'],
                      'append_found_atomics':b['found'],'policy_degree_atomics':2*b['found'] if stats else 0,
                      'policy_degree_offset_loads':4*b['found'] if stats else 0,
                      'traversal_kernel_launches':2 if pull else 1,
                      'counter_clear_bytes':24,'control_D2H_bytes':28,
                      'explicit_level_stream_syncs':1,'level_meminfo_calls':1}
                    levels.append(row)
                    for k in ['csr_edge_tests','reverse_edge_tests','push_rows','pull_distance_atomic_probes',
                      'pull_unvisited_rows','bitmap_words_zeroed','bitmap_atomic_or','distance_atomic_CAS_attempts',
                      'append_found_atomics','policy_degree_atomics','policy_degree_offset_loads','traversal_kernel_launches',
                      'counter_clear_bytes','control_D2H_bytes','explicit_level_stream_syncs','level_meminfo_calls']:total[k]+=row[k]
                    total['processed_levels']+=1;total['pull_levels' if pull else 'push_levels']+=1
                queries.append({'fixture':fixture,'query':query,'source':source,'mode':mode,'reachable':sum(x>=0 for x in distance),
                  'reason':reason,'stop_level':stop_level,**{k:total[k] for k in [
                  'processed_levels','push_levels','pull_levels','csr_edge_tests','reverse_edge_tests','push_rows',
                  'pull_distance_atomic_probes','pull_unvisited_rows','bitmap_words_zeroed','bitmap_atomic_or',
                  'distance_atomic_CAS_attempts','append_found_atomics','policy_degree_atomics','policy_degree_offset_loads',
                  'traversal_kernel_launches','counter_clear_bytes','control_D2H_bytes','explicit_level_stream_syncs','level_meminfo_calls']},
                  'total_edge_tests':total['csr_edge_tests']+total['reverse_edge_tests'],
                  'total_kernel_launches':1+total['traversal_kernel_launches'],
                  'distance_init_bytes':4*n,'output_D2H_bytes':4*n,
                  'device_payload_bytes':28*n+8*m+44+8*math.ceil(n/64)})
        for mode in MODES:
            for q in [1,2,8,32]:
                chosen=[x for x in queries if x['fixture']==fixture and x['mode']==mode and x['query']<q]
                countkeys=[k for k in chosen[0] if k not in ['fixture','query','source','mode','reachable','reason','stop_level','device_payload_bytes']]
                summary.append({'fixture':fixture,'mode':mode,'q_prefix':q,
                    **{k:sum(x[k] for x in chosen) for k in countkeys},'device_payload_bytes':chosen[0]['device_payload_bytes']})
    write_csv(OUT/'query_work.csv',queries);write_csv(OUT/'level_work.csv',levels);write_csv(OUT/'prefix_work.csv',summary)
    contrasts=[]
    for fixture in ['livejournal_sampled_4096.edges','google_sampled_1024.edges']:
        for q in [1,2,8,32]:
            bymode={x['mode']:x for x in summary if x['fixture']==fixture and x['q_prefix']==q}
            for a,b,label in [(0,6,'statistics_control'),(6,2,'direction_plus_policy_bitmap'),(2,3,'RIE_without_zero_guard'),(2,4,'zero_guard'),(4,5,'RIE_after_zero_guard'),(0,5,'bundled_ready_consumer')]:
                contrasts.append({'fixture':fixture,'q_prefix':q,'from_mode':a,'to_mode':b,'contrast':label,
                  **{'saved_'+k:bymode[a][k]-bymode[b][k] for k in ['total_edge_tests','processed_levels','total_kernel_launches','control_D2H_bytes','policy_degree_atomics']}})
    write_csv(OUT/'contrasts.csv',contrasts)
    meta={'scope':'BOUNDED_OFFLINE_WORK_ACCOUNTING_NOT_A_CORRECTNESS_SUITE_OR_TIMING_EXPERIMENT',
      'queries_accounted':len(queries),'frontier_partitions':64,'modes':MODES,'sources':SOURCES,
      'new_CPU_correctness_PASS_claims':0,'prior_402_suite_rerun':False,'new_GPU_queries_or_execution':0,
      'work_kind':'Logical code-derived operations; not instructions, DRAM/L2 transactions, hardware counters, or GPU time',
      'ordering':'Incoming adjacency order mirrors frozen source-ordered CPU scatter. Fixed frontier membership makes scheduling-independent logical edge tests.',
      'limits':'No GPU trajectory cross-check. Counts assume valid complete BFS execution; platform/launch/cache/runtime overheads remain unmeasured.',
      'source_SHA256':{p:sha((R/p).read_bytes()) for p in ['src/owner.cpp','src/kernels.cu','src/native_driver.hpp','include/independent_builder.hpp',
          'fixtures/livejournal_sampled_4096.edges','fixtures/google_sampled_1024.edges']},
      'reused_existing_reports':['reports/IMPLEMENTATION_AND_CONTRACT.md','reports/PREREGISTERED_PROTOCOL.md'],
      'new_question':'Does the ready Direction path beat an equal-stop Push control rather than only the less-terminated internal Push?'}
    (OUT/'ACCOUNTING_SCOPE.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({'q32':[x for x in summary if x['q_prefix']==32],
       'RIE_after_zero':[x for x in contrasts if x['q_prefix']==32 and x['contrast']=='RIE_after_zero_guard']},indent=2))
if __name__=='__main__':main()
