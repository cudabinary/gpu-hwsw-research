"""A single finite correctness dispatch, fail closed. No automatic retry."""
from pathlib import Path
import os,sys,subprocess,threading,time,json,hashlib,re,traceback,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parents[1]
SMI=r'C:\Windows\System32\nvidia-smi.exe'
PS=Path(os.environ['USERPROFILE'])/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'
HIDDEN=getattr(subprocess,'CREATE_NO_WINDOW',0)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=read(P/'config/GPU_MINIMAL_PILOT.json');base=read(P/'config/GPU_FIXED_BASELINE.json')
    assert plan['authorized_by_latest_user'] and plan['processes']==12 and plan['total_request_invocations']==48
    assert plan['retry']==plan['warmup']==0 and plan['watchdog_seconds']==20 and plan['dispatch_seconds']==300
    for rel,d in plan['pins'].items():assert sha(P/rel)==d,rel
    assert 'config/GPU_FIXED_BASELINE.json' in plan['pins']
    R=P/'results/GPU_PILOT';R.mkdir(exist_ok=False)
    start=time.monotonic();stop=R/'guards.stop';guards=[];handles=[];samples=[];completed=[];launched=[];active=None;retired={}
    baseline={int(p['pid']):p for p in base['processes']+base['engine_only_os_processes']}
    def observe(owned=None,preflight=False):
        if any(g.poll() is not None for g in guards):raise RuntimeError('continuous guard exited')
        p=subprocess.run([SMI,'-q','-x'],capture_output=True,timeout=2,creationflags=HIDDEN)
        if p.returncode:raise RuntimeError('SMI unavailable')
        (R/f'sample_{len(samples):04d}.xml').write_bytes(p.stdout)
        tree=ET.fromstring(p.stdout);gs=tree.findall('gpu')
        if len(gs)!=1:raise RuntimeError('ambiguous GPU')
        g=gs[0]
        def number(field):
            x=g.findtext(field);m=re.fullmatch(r'(\d+)\s*(MiB|C)?',x.strip()) if x else None
            if not m:raise RuntimeError('telemetry unavailable '+field)
            return int(m[1])
        obs=dict(elapsed_s=time.monotonic()-start,name=g.findtext('product_name'),model=g.findtext('driver_model/current_dm'),free_MiB=number('fb_memory_usage/free'),temperature_C=number('temperature/gpu_temp'),pids=[int(x.findtext('pid')) for x in g.findall('processes/process_info')],owned=owned)
        for key in ('engine','modules'):obs[key]=read(R/(key+'.status.json'))
        samples.append(obs)
        if '4060 Ti' not in obs['name'] or obs['model']!='WDDM':raise RuntimeError('GPU mismatch')
        if obs['free_MiB']<(2048 if preflight else 1536) or obs['temperature_C']>=78:raise RuntimeError('VRAM/temperature boundary')
        if set(obs['pids'])-set(baseline)-({owned} if owned else set()):raise RuntimeError('new/competing GPU PID')
        for key in ('engine','modules'):
            state=obs[key]
            if state['status']!='OK' or abs(time.time()*1000-state['epoch_ms'])>3000:raise RuntimeError('invalid/stale '+key+' telemetry: '+str(state))
        if obs['engine']['adapter_luid']!=base['adapter_luid']:raise RuntimeError('LUID mismatch')
        for e in obs['engine']['positive']:
            m=re.search(r'pid_(\d+)_',e['instance'],re.I)
            if not m:raise RuntimeError('unresolved engine PID')
            pid=int(m[1]);kind=e['instance'].lower().split('_engtype_')[-1]
            if pid==owned:continue
            if pid in retired and time.time()-retired[pid]<=3 and pid not in obs['pids']:continue
            if pid not in baseline or kind not in ('3d','copy','videodecode','videoencode','videoprocessing','legacyoverlay','vr','ofa_0','security'):raise RuntimeError('unowned GPU engine activity: '+str(e))
        return obs
    try:
        # Native binary CPU path is independent of CUDA context creation.
        abi=subprocess.run([str(P/'build/rcc_owner.exe'),'--abi'],capture_output=True,timeout=10,creationflags=HIDDEN)
        (R/'native_abi.stdout.log').write_bytes(abi.stdout)
        assert abi.returncode==0 and json.loads(abi.stdout)==read(P/'results/gpu_abi_linux.stdout.log')
        for name,extra in [('engine',['-AdapterLuid',base['adapter_luid']]),('modules',['-BaselinePath',str(P/'config/GPU_FIXED_BASELINE.json')])]:
            out=open(R/(name+'.stdout.log'),'w');err=open(R/(name+'.stderr.log'),'w');handles.extend([out,err])
            guards.append(subprocess.Popen([str(PS),'-NoProfile','-File',str(P/'tools'/(name.replace('modules','module')+'_guard.ps1')),'-StatusPath',str(R/(name+'.status.json')),'-RawPath',str(R/(name+'.raw.jsonl')),'-StopPath',str(stop)]+extra,stdout=out,stderr=err,creationflags=HIDDEN))
        until=time.monotonic()+10
        while not all((R/(n+'.status.json')).exists() for n in ('engine','modules')):
            if time.monotonic()>until or any(p.poll() is not None for p in guards):raise RuntimeError('guard startup failure')
            time.sleep(.05)
        for _ in range(3):observe(preflight=True);time.sleep(.2)
        for i,c in enumerate(plan['cases']):
            if time.monotonic()-start+20>300:raise RuntimeError('dispatch deadline')
            observe(preflight=True)
            args=[str(P/'fixtures'/c['fixture']),str(c['n']),str(c['mode'])]+list(map(str,c['sources']))
            cpu=subprocess.run([str(P/'build/rcc_owner.exe'),'--cpu-check']+args,capture_output=True,timeout=10,creationflags=HIDDEN)
            (R/f'{i:02d}.cpu.stdout.log').write_bytes(cpu.stdout);(R/f'{i:02d}.cpu.stderr.log').write_bytes(cpu.stderr)
            if cpu.returncode or b'no_driver_loaded=1' not in cpu.stdout:raise RuntimeError('native CPU preflight failed')
            ready=R/f'{i:02d}.ready';ack=R/f'{i:02d}.ack';cmd=[str(P/'build/rcc_owner.exe'),'--execute']+args
            env=dict(os.environ,TCSC_GPU_APPROVED_TOKEN='HUMAN_APPROVED_FINITE_PLAN',TCSC_CUBIN=str(P/'build/rcc_kernels.cubin'),TCSC_READY=str(ready),TCSC_ACK=str(ack),CUDA_CACHE_DISABLE='1')
            save(R/f'{i:02d}.command.json',dict(command=cmd,case=c))
            began=time.monotonic();reason=[]
            with open(R/f'{i:02d}.stdout.log','w') as out,open(R/f'{i:02d}.stderr.log','w') as err:
                active=subprocess.Popen(cmd,env=env,stdout=out,stderr=err,creationflags=HIDDEN);child=active;launched.append(dict(index=i,pid=child.pid))
                def timeout():
                    reason.append('20s child watchdog')
                    if child.poll() is None:child.kill()
                timer=threading.Timer(20,timeout);timer.daemon=True;timer.start();acknowledged=False
                try:
                    while child.poll() is None:
                        obs=observe(child.pid)
                        if time.monotonic()-start>300:raise RuntimeError('campaign deadline')
                        if ready.exists() and not acknowledged:
                            if int(ready.read_text())!=child.pid or child.pid not in obs['pids']:raise RuntimeError('CUDA PID handshake unavailable')
                            ack.write_text(str(child.pid));acknowledged=True
                        time.sleep(.05)
                    if reason or child.returncode or not acknowledged:raise RuntimeError('CUDA child failure: '+str(reason or child.returncode))
                finally:timer.cancel()
            if 'CONTEXT_RELEASED_SYNC_OK' not in (R/f'{i:02d}.stderr.log').read_text():raise RuntimeError('context cleanup unconfirmed')
            retired[child.pid]=time.time()
            if child.pid in observe()['pids']:raise RuntimeError('GPU context still present')
            rows=[json.loads(line) for line in (R/f'{i:02d}.stdout.log').read_text().splitlines() if line.startswith('{')]
            bfs=[x for x in rows if x['kind']=='BFS'];cancels=[x for x in rows if x['kind']=='cancel']
            assert len(bfs)==3 and len(cancels)==1 and all(x['status']=='PASS' and x['device_payload_bytes']<=32<<20 for x in bfs)
            completed.append(dict(case=c,results=rows,seconds=time.monotonic()-began));active=None
            print('GPU_PASS',len(completed),'/ 12',flush=True)
        save(R/'RECEIPT.json',dict(status='PASS',processes=len(completed),BFS=36,cancellations=12,seconds=time.monotonic()-start,completed=completed,pins=plan['pins']))
    except BaseException as e:
        uncertain=active is not None
        if active is not None and active.poll() is None:active.kill();active.wait(timeout=3)
        save(R/'STOP.json',dict(status='STOPPED_NO_RETRY',reason=str(e),launched=launched,completed=completed,seconds=time.monotonic()-start,context='UNCONFIRMED_NO_MORE_GPU_USE' if uncertain else 'NO_ACTIVE_WORKER',traceback=traceback.format_exc()))
        print('GPU_STOP_NO_RETRY',str(e),flush=True);raise
    finally:
        save(R/'TELEMETRY.json',samples);stop.touch()
        for p in guards:
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
        for f in handles:f.close()
if __name__=='__main__':main()
