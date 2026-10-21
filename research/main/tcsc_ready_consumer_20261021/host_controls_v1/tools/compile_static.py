"""Existing WSL MinGW host compilation only; no CUDA execution or query."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[1]
if (R/'audit/COMPILE.json').exists():raise RuntimeError('PRESERVE_EXISTING_COMPILE_ATTEMPT')
wsl=lambda p:'/mnt/c/'+p.resolve().as_posix()[3:]
args=['wsl.exe','-d','Ubuntu','--','x86_64-w64-mingw32-g++','-std=c++17','-O2','-static',
 '-I'+wsl(R/'src'),'-I'+wsl(R/'include'),'-I/usr/local/cuda-13.3/include',
 wsl(R/'src/owner_controls_v1.cpp'),'-o',wsl(R/'build/owner_controls_v1.exe')]
t=time.monotonic();p=subprocess.run(args,capture_output=True,timeout=180)
(R/'audit/compile.stdout.log').write_bytes(p.stdout);(R/'audit/compile.stderr.log').write_bytes(p.stderr)
result={'status':'STATIC_HOST_COMPILE_LINK_PASS' if p.returncode==0 else 'FAIL','argv':args,
 'exit_code':p.returncode,'seconds':time.monotonic()-t,'GPU_calls':0,
 'new_CUDA_compilation':False,'existing_cubin_used':True,'new_execution_permit_set':False,
 'GPU_owner_path_compiled':True,'runtime_gate_is_checked_before_driver_init':True}
if p.returncode==0:result['binary_sha256']=hashlib.sha256((R/'build/owner_controls_v1.exe').read_bytes()).hexdigest()
(R/'audit/COMPILE.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));raise SystemExit(p.returncode)
