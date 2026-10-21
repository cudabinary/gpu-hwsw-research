from pathlib import Path
import hashlib,json,os,subprocess,time,shutil
R=Path(__file__).resolve().parents[1]
env=dict(os.environ);env.pop('TCSC_GPU_APPROVED_TOKEN',None)
cases=[]
for fixture,n,q in [('gpu_micro7.edges',7,3),('livejournal_sampled_4096.edges',4096,32),('google_sampled_1024.edges',1024,32)]:
    for mode in [0,2,3,4,5,6]:
        argv=[str(R/'build/round_owner.exe'),'--cpu-check',str(R/'fixtures'/fixture),str(n),str(mode),str(q)]
        p=subprocess.run(argv,env=env,capture_output=True,timeout=15)
        entry={'fixture':fixture,'n':n,'mode':mode,'q':q,'exit_code':p.returncode}
        if p.returncode==0:entry['result']=json.loads(p.stdout)
        else:entry['stderr']=p.stderr.decode(errors='replace')
        cases.append(entry)
        if p.returncode:break
negative=[]
for mode,q in [(1,3),(7,3),(0,4),(0,0)]:
    p=subprocess.run([str(R/'build/round_owner.exe'),'--cpu-check',str(R/'fixtures/gpu_micro7.edges'),'7',str(mode),str(q)],env=env,capture_output=True,timeout=10)
    negative.append({'mode':mode,'q':q,'rejected':p.returncode!=0})
abi=subprocess.run([str(R/'build/round_owner.exe'),'--abi'],env=env,capture_output=True,timeout=10,check=True)
result={'status':'PASS' if len(cases)==18 and all(c['exit_code']==0 for c in cases) and all(x['rejected'] for x in negative) else 'FAIL',
    'new_cpu_distance_arrays':sum(c['q'] for c in cases if c['exit_code']==0),'gpu_calls':0,'cases':cases,'negative':negative,'abi':json.loads(abi.stdout)}
(R/'audit/CPU_PREFLIGHT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if result['status']!='PASS':raise SystemExit(1)
old=R/'input/archived_safety/roots/WIN_TASK/TCSC_RCC_RIE_CPU_STATIC_20261021'
for name in ['engine_guard.ps1','module_guard.ps1','process_guard.cpp','adapter_luid.cpp']:
    shutil.copyfile(old/'tools'/name,R/'tools'/name)
shutil.copyfile(old/'build/process_guard.exe',R/'build/process_guard.exe')
