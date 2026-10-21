from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[1]
args=['x86_64-w64-mingw32-g++','-std=c++17','-O2','-static','-Isrc','-Iinclude','-I/usr/local/cuda-13.3/include','src/owner.cpp','-o','build/round_owner.exe']
t=time.monotonic();p=subprocess.run(args,cwd=R,capture_output=True,timeout=180)
(R/'audit/compile.stdout.log').write_bytes(p.stdout);(R/'audit/compile.stderr.log').write_bytes(p.stderr)
receipt={'argv':args,'exit_code':p.returncode,'seconds':time.monotonic()-t,'gpu_calls':0}
if p.returncode==0:receipt['binary_sha256']=hashlib.sha256((R/'build/round_owner.exe').read_bytes()).hexdigest()
(R/'audit/COMPILE.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
raise SystemExit(p.returncode)
