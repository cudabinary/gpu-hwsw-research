from pathlib import Path
from collections import deque
import hashlib,json,sys
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
modes={0:'PUSH_EARLY_N',2:'DO_EARLY_N',3:'DO_EARLY_N_RIE',4:'DO_EARLY_N_FRONTIER_ZERO',5:'DO_EARLY_N_FRONTIER_ZERO_RIE',6:'PUSH_STATS_EARLY_N'}
cases=[{'phase':'FUNCTIONAL','fixture':'gpu_micro7.edges','n':7,'mode':mode,'q':3,'block':-1} for mode in modes]
orders=[[0,2,3,4,5,6],[6,5,4,3,2,0],[3,4,5,6,0,2]]
inputs=[('livejournal_sampled_4096.edges',4096),('google_sampled_1024.edges',1024)]
for block,order in enumerate(orders):
    for fixture,n in (inputs if block!=1 else list(reversed(inputs))):
        for mode in order:cases.append({'phase':'READY_TIMING','fixture':fixture,'n':n,'mode':mode,'q':32,'block':block})
if '--finish-pins' not in sys.argv:
    upper=[]
    for fixture,n in inputs:
        adj=[[] for _ in range(n)]
        for line in (R/'fixtures'/fixture).read_text().splitlines():
            if line.startswith('#') or not line.strip():continue
            parts=line.split()
            try:u,v=map(int,parts[:2])
            except ValueError:continue
            adj[u].append(v)
        levels=[]
        for source in [17*i for i in range(32)]:
            d=[-1]*n;d[source]=0;q=deque([source])
            while q:
                u=q.popleft()
                for v in adj[u]:
                    if d[v]<0:d[v]=d[u]+1;q.append(v)
            levels.append(max(d)+1)
        bound=sum(1+2*x for x in levels)
        assert bound<2040
        upper.append({'fixture':fixture,'max_processed_levels_bound':max(levels),'per_process_kernel_launch_upper_bound':bound,'kind':'CPU graph arithmetic, not measured duration'})
    protocol={'authorized_by_latest_user':True,'processes':42,'completed_BFS_max':1170,'cancellations_max':6,
        'total_request_invocations':1176,'retry':0,'warmup':0,'watchdog_seconds':20,'dispatch_seconds':900,
        'gpu_session_max_seconds':1800,'workspace_bytes_max':32<<20,'start_free_MiB_min':2048,
        'run_free_MiB_min':1536,'temperature_C_exclusive_max':78,'telemetry_staleness_ms_max':3000,
        'modes':modes,'primary_comparison':[5,0],'alpha':15,'beta':24,'sources_q32':[17*i for i in range(32)],
        'q_prefixes':[1,2,8,32],'primary_gate':'LJ mode5/mode0 q32 owned-ready prefix ratio <0.95 in ALL three paired blocks; exploratory finite gate, not a confidence interval',
        'builder_GPU_attempts':0,'Nsight_processes':0,'new_CUDA_kernels':0,'RCC_queries':0,
        'same_resident_reverse_for_push':True,'timing_boundary':'Initialized resident immutable graph+reverse; each query includes initialization, safety checks, host synchronization, D2H and owned output. CPU references, work reconstruction, validation and file/log output outside batch.',
        'work_kind':'CPU code-exact reconstruction cross-checked against actual GPU seen/levels/reason; not hardware transactions',
        'arrival_trace':'NONE; fixed-batch amortization only','cases':cases,'kernel_upper_bounds':upper,
        'helper_process_accounting':{'CUDA_workers_max':42,'independent_CPU_watchdogs_max':42,'continuous_CPU_guard_processes':3,'adapter_query_processes':1,'module_inventory_and_nvidia_smi_queries':'finite while dispatch active, separate telemetry role; actual counts in raw logs'},
        'failure':'Stop on exact-output mismatch, CUDA error, OOM, unknown GPU PID, competing work, guard error/staleness, watchdog, temperature or VRAM boundary. No retry or rule relaxation.'}
    p=R/'config/PREREGISTERED_PLAN.json';p.write_text(json.dumps(protocol,indent=2));(R/'audit/PREREGISTRATION_SHA256.txt').write_text(sha(p)+'\n');print(json.dumps({'status':'PREREGISTERED','cases':len(cases),'BFS_max':1170,'kernel_bounds':upper}));raise SystemExit
protocol=json.loads((R/'config/PREREGISTERED_PLAN.json').read_text())
assert sha(R/'config/PREREGISTERED_PLAN.json')==(R/'audit/PREREGISTRATION_SHA256.txt').read_text().strip()
assert json.loads((R/'audit/CPU_PREFLIGHT.json').read_text())['status']=='PASS'
assert json.loads((R/'audit/WATCHDOG_TEST.json').read_text())['status']=='PASS'
names=['build/round_owner.exe','build/rcc_kernels.cubin','build/process_guard.exe','build/adapter_luid.exe',
       'src/owner.cpp','src/abi.hpp','src/kernels.cu','src/native_driver.hpp','config/GPU_FIXED_BASELINE.json']
names += ['tools/'+n for n in ['run_gpu_round.py','engine_guard.ps1','module_guard.ps1','wsl_guard.py','child_watchdog.py','watchdog_support.py']]
names += ['fixtures/'+n for n in ['gpu_micro7.edges','livejournal_sampled_4096.edges','google_sampled_1024.edges']]
protocol['pins']={name:sha(R/name) for name in names};protocol['preregistered_plan_sha256']=sha(R/'config/PREREGISTERED_PLAN.json')
(R/'config/ROUND_PLAN.json').write_text(json.dumps(protocol,indent=2));print(json.dumps({'status':'DISPATCH_PINNED','preregistered_sha256':protocol['preregistered_plan_sha256']}))
