from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
OUT=R/'audit/native_nvml_readonly_20261021';OUT.mkdir(exist_ok=False)
commands=[('native_nvml',[sys.executable,str(R/'tools/native_nvml_count_readonly.py')]),
          ('native_smi_compute',[r'C:\Windows\System32\nvidia-smi.exe','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv']),
          ('native_smi_driver',[r'C:\Windows\System32\nvidia-smi.exe','--query-gpu=name,driver_version,driver_model.current','--format=csv'])]
rows=[]
for label,args in commands:
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        p=subprocess.run(args,capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        (OUT/(label+'.stdout.log')).write_bytes(p.stdout);(OUT/(label+'.stderr.log')).write_bytes(p.stderr)
        row={'label':label,'started_utc':start,'ended_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'exit_code':p.returncode,
             'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()}
        if label=='native_nvml' and p.returncode==0:row['observation']=json.loads(p.stdout)
        elif p.returncode==0:row['output_text']=p.stdout.decode(errors='replace')
        rows.append(row)
    except subprocess.TimeoutExpired:
        rows.append({'label':label,'status':'TIMED_OUT_NO_RETRY'});break
receipt={'status':'READ_ONLY_DIAGNOSTIC_RECORDED','commands':rows,'new_GPU_BFS':0,'CUDA_workers':0,'guard_changes':0,
         'denied_process_query_retries':0,'new_permissions_or_security_changes':0,'benchmark_resume_allowed':False,
         'concurrent_CUDA_absence_or_isolation':'NOT_PROVED_BY_THIS_DIAGNOSTIC'}
(OUT/'RESULT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
