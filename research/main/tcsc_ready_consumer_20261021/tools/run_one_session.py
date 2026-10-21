from pathlib import Path
import datetime,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
PS=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'
start=time.monotonic();stamp={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'session_gpu_wall_limit_seconds':1800,'CUDA_workers_started':0}
with (R/'audit/GPU_SESSION_START.json').open('x') as f:json.dump(stamp,f,indent=2)
def call(label,argv,timeout):
    p=subprocess.run(argv,cwd=R,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
    (R/'audit'/(label+'.stdout.log')).write_bytes(p.stdout);(R/'audit'/(label+'.stderr.log')).write_bytes(p.stderr)
    if p.returncode:raise RuntimeError(label+'_FAILED_EXIT_'+str(p.returncode))
try:
    call('fresh_gpu_baseline',[str(PS),'-NoProfile','-File',str(R/'tools/freeze_gpu_baseline.ps1')],30)
    call('finish_dispatch_pins',[sys.executable,str(R/'tools/prepare_plan.py'),'--finish-pins'],15)
    if time.monotonic()-start+930>1800:raise RuntimeError('GPU_SESSION_BUDGET')
    call('gpu_round',[sys.executable,str(R/'tools/run_gpu_round.py')],930)
    state={'status':'FINITE_SESSION_COMPLETE','wall_seconds':time.monotonic()-start}
except BaseException as e:
    state={'status':'STOPPED_NO_RETRY','reason':str(e),'wall_seconds':time.monotonic()-start,
           'resume_GPU_automatically':False,'CUDA_worker_execution_status':'Inspect GPU_ROUND/STOP.json; none if round directory absent'}
finally:
    if (R/'results/GPU_ROUND').exists():(R/'results/GPU_ROUND/guards.stop').touch()
    (R/'audit/GPU_SESSION_RESULT.json').write_text(json.dumps(state,indent=2))
    print(json.dumps(state),flush=True)
if state['status']!='FINITE_SESSION_COMPLETE':raise SystemExit(1)
