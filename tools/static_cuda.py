from pathlib import Path
import subprocess,json,time,hashlib
root=Path(__file__).resolve().parents[1]
out=root/'build/static';out.mkdir(parents=True,exist_ok=True)
logs=root/'results'/('static_cuda_'+str(time.time_ns()));logs.mkdir(parents=True,exist_ok=False)
commands=[
 ('cubin',['/usr/local/cuda-13.3/bin/nvcc','-std=c++17','-O2','-arch=sm_89','--cubin','vendor/rcc_20261021/cuda/kernels.cu','-o',str(out/'rcc_kernels.cubin')]),
 ('native_owner',['x86_64-w64-mingw32-g++','-std=c++17','-O2','-static','-Ivendor/rcc_20261021/frozen/consumer','-I/usr/local/cuda-13.3/include','vendor/rcc_20261021/cuda/owner.cpp','-o',str(out/'rcc_owner.exe')])]
rows=[]
for name,args in commands:
 start=time.monotonic();r=subprocess.run(args,cwd=root,capture_output=True,timeout=180)
 (logs/(name+'.stdout.log')).write_bytes(r.stdout);(logs/(name+'.stderr.log')).write_bytes(r.stderr)
 rows.append({'name':name,'argv':args,'code':r.returncode,'seconds':time.monotonic()-start})
 (logs/'COMMANDS.json').write_text(json.dumps(rows,indent=2))
 if r.returncode:raise SystemExit('static compile failed; no auto retry')
report={'status':'PASS','scope':'unchanged historical kernels and native owner, NOT common RCC API backend','GPU_queries':0,'GPU_kernel_executions':0,'artifacts':{p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in out.iterdir() if p.is_file()}}
(logs/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(root/'results/CUDA_STATIC.json').write_text(json.dumps(report,indent=2))
