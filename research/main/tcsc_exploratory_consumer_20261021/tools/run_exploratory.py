"""One explicitly authorized ISOLATION_UNVERIFIED exploratory GPU session.

No foreign process-memory/module inspection, privilege change or strict override.
Only observable research/compute activity is rejected; absence is never proved.
"""
from pathlib import Path
from ctypes import wintypes as W
import argparse,ctypes,datetime as dt,hashlib,json,os,re,struct,subprocess,threading,time,traceback,xml.etree.ElementTree as ET
from collections import deque
import watchdog_support
P=Path(__file__).resolve().parents[1]
SMI=r'C:\Windows\System32\nvidia-smi.exe'
PS=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'
HIDDEN=subprocess.CREATE_NO_WINDOW
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path,obj):path.write_text(json.dumps(obj,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--exploratory-isolation-unverified',action='store_true',required=True);parser.parse_args()
    plan=load(P/'config/PLAN.json')
    assert plan['contract']=='ISOLATION_UNVERIFIED' and plan['explicit_user_authorized']
    assert len(plan['cases'])==9 and plan['maximum_full_BFS_arrays']==201
    assert plan['warmup']==plan['automatic_payload_or_GPU_retries']==0
    assert sha(P/'config/PLAN.json')==(P/'audit/PLAN_SHA256.txt').read_text().split()[0]
    for rel,digest in plan['pins'].items():assert sha(P/rel)==digest,rel
    strict=P.parent/'MAIN_TCSC_READY_CONSUMER_ROUND_20261021'
    for rel,digest in plan['strict_preservation_pins'].items():assert sha(strict/rel)==digest,rel
    R=P/'results/EXPLORATORY_SESSION';R.mkdir(exist_ok=False)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE];kernel.CreateFileW.restype=W.HANDLE
    kernel.CloseHandle.argtypes=[W.HANDLE]
    lock=kernel.CreateFileW(str(R/'SESSION.lock'),0xC0000000,0,None,4,0x80,None)
    if lock==ctypes.c_void_p(-1).value:raise RuntimeError('SESSION_LOCK_UNAVAILABLE')
    start=time.monotonic();save(R/'SESSION_START.json',{'started_utc':utc(),'contract':'ISOLATION_UNVERIFIED','plan_sha256':sha(P/'config/PLAN.json'),'one_session_only':True})
    active=None;engine=None;engine_handles=[];watchdogs=[];samples=[];completed=[];launched=[]
    baseline_pids=set();baseline_3d={};retired={};retired_disappeared=set();context_state='NO_CUDA_WORKER_CREATED';worker_seconds=0.0
    stop_path=R/'engine.stop';cache={};oracle_started=time.monotonic()
    # Fixed exact Python references precede CUDA and are reused across workers.
    for fixture,n,sources in [('gpu_micro7.edges',7,[0,1,4]),('livejournal_sampled_4096.edges',4096,[17*i for i in range(32)])]:
        adj=[[] for _ in range(n)]
        for line in (P/'fixtures'/fixture).read_text().splitlines():
            if line and line[0] not in '#%':u,v=map(int,line.split());adj[u].append(v)
        for source in sources:
            distance=[-1]*n;distance[source]=0;queue=deque([source])
            while queue:
                u=queue.popleft()
                for v in adj[u]:
                    if distance[v]<0:distance[v]=distance[u]+1;queue.append(v)
            cache[(fixture,source)]=struct.pack('<'+'i'*n,*distance)
    oracle_seconds=time.monotonic()-oracle_started
    def observe(owned=None,preflight=False,initializing=False):
        if len(samples)>=plan['maximum_nvidia_smi_samples']:raise RuntimeError('TELEMETRY_SAMPLE_CAP')
        if engine is not None and engine.poll() is not None:raise RuntimeError('ENGINE_MONITOR_EXITED')
        q=subprocess.run([SMI,'-q','-x'],capture_output=True,timeout=2,creationflags=HIDDEN)
        index=len(samples);(R/f'telemetry_{index:04d}.xml').write_bytes(q.stdout)
        (R/f'telemetry_{index:04d}.stderr.log').write_bytes(q.stderr)
        if q.returncode:raise RuntimeError('NVIDIA_SMI_UNAVAILABLE')
        tree=ET.fromstring(q.stdout);gpus=tree.findall('gpu')
        if len(gpus)!=1:raise RuntimeError('DEVICE_COUNT_AMBIGUOUS')
        gpu=gpus[0]
        def number(path):
            value=gpu.findtext(path);m=re.fullmatch(r'(\d+)\s*(MiB|C|%)?',value.strip()) if value else None
            if not m:raise RuntimeError('REQUIRED_TELEMETRY_UNAVAILABLE_'+path)
            return int(m[1])
        processes=[]
        for item in gpu.findall('processes/process_info'):
            pid=item.findtext('pid')
            if not pid or not pid.isdecimal():raise RuntimeError('UNRESOLVED_GPU_PID')
            processes.append({'pid':int(pid),'type':item.findtext('type'),'name':item.findtext('process_name'),'used_memory':item.findtext('used_memory')})
        observation={'utc':utc(),'elapsed_s':time.monotonic()-start,'contract':'ISOLATION_UNVERIFIED',
          'name':gpu.findtext('product_name'),'driver_version':tree.findtext('driver_version'),'model':gpu.findtext('driver_model/current_dm'),
          'free_MiB':number('fb_memory_usage/free'),'temperature_C':number('temperature/gpu_temp'),
          'utilization_percent':number('utilization/gpu_util'),'processes':processes,'owned_PID':owned,
          'external_CUDA_absence':'UNKNOWN','WSL_context_visibility':'UNKNOWN','enforced_exclusivity':False}
        if '4060 Ti' not in observation['name'] or observation['model']!='WDDM':raise RuntimeError('DEVICE_OR_DRIVER_MODEL_CHANGED')
        if observation['free_MiB']<(2048 if preflight else 1536) or observation['temperature_C']>=78:raise RuntimeError('VRAM_OR_TEMPERATURE_BOUNDARY')
        if samples and any(observation[k]!=samples[0][k] for k in ['name','driver_version','model']):raise RuntimeError('DEVICE_ENVIRONMENT_CHANGED')
        now=time.time();pids={x['pid'] for x in processes}
        cleanup_pids=set(retired)-retired_disappeared
        for item in processes:
            if item['pid']!=owned and re.search(plan['known_research_process_name_pattern'],item['name'] or ''):
                if item['pid'] not in cleanup_pids:raise RuntimeError('OBSERVED_OTHER_RESEARCH_GPU_PROCESS')
            if item['pid']!=owned and item['pid'] not in cleanup_pids and item['type']=='C':raise RuntimeError('OBSERVED_UNOWNED_COMPUTE_CONTEXT')
        if (not initializing or baseline_pids) and pids-baseline_pids-({owned} if owned else set())-cleanup_pids:raise RuntimeError('ABRUPT_NEW_NONOWNED_GPU_PID')
        if engine is not None:
            e=load(R/'engine.status.json');observation['engine']=e
            if e['status']!='OK' or abs(time.time()*1000-e['epoch_ms'])>3000:raise RuntimeError('ENGINE_TELEMETRY_INVALID_OR_STALE')
            for item in e['positive']:
                found=re.search(r'pid_(\d+)_',item['instance'],re.I)
                if not found:raise RuntimeError('UNRESOLVED_ENGINE_PID')
                pid=int(found[1]);kind=item['instance'].lower().split('_engtype_')[-1]
                if pid==owned:continue
                if pid in retired and now-retired[pid]<=3 and pid not in pids:continue
                if 'compute' in kind or 'cuda' in kind:raise RuntimeError('OBSERVED_UNOWNED_COMPUTE_ENGINE_ACTIVITY')
                if '3d' in kind:
                    if initializing:baseline_3d[item['instance']]=max(baseline_3d.get(item['instance'],0),item['value'])
                    elif item['value']>max(20,baseline_3d.get(item['instance'],0)+15):raise RuntimeError('ABRUPT_BACKGROUND_3D_ACTIVITY')
        samples.append(observation)
        return observation
    try:
        dxgi=subprocess.run([str(P/'build/adapter_luid.exe')],capture_output=True,timeout=5,creationflags=HIDDEN)
        (R/'dxgi.stdout.jsonl').write_bytes(dxgi.stdout);(R/'dxgi.stderr.log').write_bytes(dxgi.stderr)
        if dxgi.returncode:raise RuntimeError('NVIDIA_DXGI_MAPPING_UNAVAILABLE')
        adapter=json.loads(dxgi.stdout);baseline=observe(preflight=True,initializing=True)
        baseline_pids={x['pid'] for x in baseline['processes']}
        out=open(R/'engine.stdout.log','w');err=open(R/'engine.stderr.log','w');engine_handles=[out,err]
        engine=subprocess.Popen([str(PS),'-NoProfile','-File',str(P/'tools/engine_guard.ps1'),'-StatusPath',str(R/'engine.status.json'),'-RawPath',str(R/'engine.raw.jsonl'),'-StopPath',str(stop_path),'-AdapterLuid',adapter['luid']],stdout=out,stderr=err,creationflags=HIDDEN)
        deadline=time.monotonic()+8
        while not (R/'engine.status.json').exists():
            if time.monotonic()>deadline or engine.poll() is not None:raise RuntimeError('ENGINE_MONITOR_STARTUP_FAILURE')
            time.sleep(.05)
        for _ in range(3):observe(preflight=True,initializing=True);time.sleep(.2)
        # The first sample is background observation, not a no-compute proof.
        # New PIDs even during startup stop instead of expanding that set.
        save(R/'EXPLORATORY_BACKGROUND.json',{'contract':'ISOLATION_UNVERIFIED','sampled_PIDs':sorted(baseline_pids),'trusted_no_compute_allowlist':False,'unreadable_fields':'UNKNOWN','3D_baseline':baseline_3d})
        for index,case in enumerate(plan['cases']):
            if time.monotonic()-start+30>600:raise RuntimeError('ONE_SESSION_DEADLINE')
            if case['phase']=='EXPLORATORY_TIMING' and (len(completed)<3 or any(x['case']['phase']!='SMOKE' for x in completed[:3])):raise RuntimeError('SMOKE_GATE_NOT_COMPLETE')
            observe(preflight=True)
            ready=R/f'{index:02d}.ready';ack=R/f'{index:02d}.ack';output=R/f'{index:02d}.distances.bin'
            command=[str(P/'build/owner_controls_v1.exe'),'--execute',str(P/'fixtures'/case['fixture']),str(case['n']),str(case['mode']),str(case['q'])]
            env={k:v for k,v in os.environ.items() if not k.startswith('TCSC_')}
            env.update(TCSC_GPU_APPROVED_TOKEN='HUMAN_APPROVED_FINITE_PLAN',TCSC_HOST_CONTROLS_V1_APPROVED='NEW_REVIEWED_FINITE_PLAN',TCSC_CUBIN=str(P/'build/rcc_kernels.cubin'),TCSC_READY=str(ready),TCSC_ACK=str(ack),TCSC_DISTANCE_OUT=str(output),CUDA_CACHE_DISABLE='1')
            save(R/f'{index:02d}.command.json',{'case':case,'command':command,'contract':'ISOLATION_UNVERIFIED','fresh_child_only_permits':True,'preexisting_TCSC_variables_inherited':False})
            began=time.monotonic();reason=[];context_state='OWNED_CONTEXT_END_UNCONFIRMED'
            with open(R/f'{index:02d}.stdout.log','w') as log,open(R/f'{index:02d}.stderr.log','w') as errors:
                active=subprocess.Popen(command,env=env,stdout=log,stderr=errors,creationflags=HIDDEN);child=active
                launched.append({'index':index,'case':case,'pid':child.pid,'started_utc':utc()})
                watchdog_path=R/f'{index:02d}.watchdog.json'
                watchdog=watchdog_support.start(child,watchdog_path,watchdog_support.now_tick()+20000);watchdogs.append(watchdog)
                def timeout():
                    reason.append('CHILD_WATCHDOG_20_SECONDS')
                    if child.poll() is None:child.kill()
                timer=threading.Timer(20,timeout);timer.daemon=True;timer.start();acknowledged=False
                try:
                    while child.poll() is None:
                        obs=observe(owned=child.pid)
                        if time.monotonic()-start>=600:raise RuntimeError('ONE_SESSION_DEADLINE')
                        if watchdog.poll() is not None and (child.poll() is None or load(watchdog_path)['status']!='CHILD_EXITED'):raise RuntimeError('INDEPENDENT_WATCHDOG_FAILURE')
                        if ready.exists() and not acknowledged and watchdog_path.exists() and load(watchdog_path)['status']=='WATCHING':
                            if int(ready.read_text())!=child.pid:raise RuntimeError('OWNED_READY_PID_MISMATCH')
                            if child.pid in {x['pid'] for x in obs['processes']}:ack.write_text(str(child.pid));acknowledged=True
                        time.sleep(.05)
                    if reason or child.returncode or not acknowledged:raise RuntimeError('CUDA_CHILD_FAILED_'+str(reason or child.returncode))
                finally:timer.cancel()
                watchdog.wait(timeout=3)
                if watchdog.returncode or load(watchdog_path)['status']!='CHILD_EXITED':raise RuntimeError('WATCHDOG_EXIT_BOUNDARY')
            if 'CONTEXT_RELEASED_SYNC_OK' not in (R/f'{index:02d}.stderr.log').read_text():raise RuntimeError('CUDA_CONTEXT_RELEASE_UNCONFIRMED')
            retired[child.pid]=time.time();end_deadline=time.monotonic()+3
            while child.pid in {x['pid'] for x in observe()['processes']}:
                if time.monotonic()>end_deadline:raise RuntimeError('OWNED_CONTEXT_PID_STILL_REPORTED')
                time.sleep(.1)
            retired_disappeared.add(child.pid)
            context_state='CONTEXT_RELEASE_MARKER_AND_PID_ABSENCE_CONFIRMED';worker_seconds+=time.monotonic()-began
            rows=[json.loads(line) for line in (R/f'{index:02d}.stdout.log').read_text().splitlines() if line.startswith('{')]
            bfs=[x for x in rows if x['kind']=='BFS'];batch=[x for x in rows if x['kind']=='BATCH']
            if len(bfs)!=case['q'] or len(batch)!=1 or any(x['status']!='PASS' for x in rows):raise RuntimeError('GPU_RESULT_ROWS_INVALID')
            if batch[0]['device_payload_bytes']>32<<20 or batch[0]['cancel_tests']!=int(case['q']==3):raise RuntimeError('WORKSPACE_OR_CANCEL_CONTRACT')
            raw=output.read_bytes();expected_sources=[0,1,4] if case['q']==3 else [17*i for i in range(32)]
            if len(raw)!=4*case['n']*case['q']:raise RuntimeError('FULL_OUTPUT_LENGTH')
            for query,source in enumerate(expected_sources):
                if raw[4*case['n']*query:4*case['n']*(query+1)]!=cache[(case['fixture'],source)]:raise RuntimeError('INDEPENDENT_PYTHON_GPU_DISTANCE_MISMATCH')
            completed.append({'index':index,'case':case,'results':rows,'worker_wall_upper_bound_seconds':time.monotonic()-began,'distance_sha256':sha(output),'Python_full_array_check':'PASS'})
            active=None;save(R/'PROGRESS.json',{'contract':'ISOLATION_UNVERIFIED','completed':len(completed),'BFS':sum(x['case']['q'] for x in completed),'context':context_state})
            print('EXPLORATORY_PASS',len(completed),'/9',flush=True)
        save(R/'RECEIPT.json',{'status':'EXPLORATORY_CORRECTNESS_PASS','contract':'ISOLATION_UNVERIFIED','completed_utc':utc(),
          'processes':len(completed),'BFS':sum(x['case']['q'] for x in completed),'init_only_cancellations':3,
          'whole_session_seconds':time.monotonic()-start,'CUDA_worker_wall_upper_bound_seconds':worker_seconds,
          'Python_reference_preparation_seconds':oracle_seconds,'completed':completed,'telemetry_samples':len(samples),
          'protected_process_module_memory_queries':0,'security_or_driver_changes':0,'profiler_runs':0,'retries':0,
          'external_CUDA_absence':'UNKNOWN','WSL_context_visibility':'UNKNOWN','enforced_exclusivity':False,
          'context_end':context_state,'timing_claim':'EXPLORATORY_ONLY_NOT_ISOLATED_OR_CAUSAL','pins':plan['pins']})
    except BaseException as exc:
        if active is not None and active.poll() is None:active.kill();active.wait(timeout=3)
        save(R/'STOP.json',{'status':'STOPPED_NO_RETRY','contract':'ISOLATION_UNVERIFIED','reason':str(exc),
          'context':context_state,'launched':launched,'completed':completed,'seconds':time.monotonic()-start,'traceback':traceback.format_exc()})
        print('EXPLORATORY_STOP',str(exc),flush=True);raise
    finally:
        save(R/'TELEMETRY.json',samples);stop_path.touch()
        if engine is not None:
            try:engine.wait(timeout=3)
            except subprocess.TimeoutExpired:engine.kill();engine.wait(timeout=3)
        for w in watchdogs:
            try:w.wait(timeout=3)
            except subprocess.TimeoutExpired:w.kill();w.wait(timeout=3)
        for handle in engine_handles:handle.close()
        kernel.CloseHandle(lock)
        unchanged={rel:sha(strict/rel)==digest for rel,digest in plan['strict_preservation_pins'].items()}
        save(R/'STRICT_PRESERVATION_CHECK.json',{'unchanged':unchanged,'all_preserved':all(unchanged.values())})
if __name__=='__main__':main()
