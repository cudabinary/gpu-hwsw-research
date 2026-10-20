from pathlib import Path
import subprocess,json,hashlib,time,os
root=Path(__file__).resolve().parents[1]
os.chdir(root)
build=root/'build';build.mkdir(exist_ok=True)
results=root/'results'/('run_'+str(time.time_ns()));results.mkdir(parents=True)
commands=[]
def run(name,args,timeout=120):
 start=time.monotonic();r=subprocess.run(args,capture_output=True,timeout=timeout)
 (results/(name+'.stdout.log')).write_bytes(r.stdout)
 (results/(name+'.stderr.log')).write_bytes(r.stderr)
 commands.append({'name':name,'argv':args,'returncode':r.returncode,'seconds':time.monotonic()-start})
 (results/'COMMANDS.json').write_text(json.dumps(commands,indent=2))
 if r.returncode: raise SystemExit(f'{name} failed; logs preserved; no auto retry')
 return r.stdout.decode()
flags=['g++','-std=c++20','-O2','-Wall','-Wextra','-pthread','-Iapi','-Ivendor/rcc_20261021/include','-Ivendor/rcc_20261021/frozen/bridge','-Ivendor/rcc_20261021/frozen/consumer']
run('build_graph',flags+['-fPIC','-shared','src/graph.cpp','-o','build/libgraph.so'],180)
for kind,name in [(0,'baseline'),(1,'rcc_table'),(2,'rcc_last')]:
 run('build_'+name,flags+['-DRCC_KIND='+str(kind),'-fPIC','-shared','src/cpu_module.cpp','vendor/rcc_20261021/frozen/consumer/consumers.cpp','-o','build/'+name+'.so'],180)
run('build_main_client',flags+['tests/main_client.cpp','-Lbuild','-lgraph','-Wl,-rpath,$ORIGIN','-ldl','-o','build/main_client'],180)
sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
client_sha=sha(build/'main_client');results_list=[]
for name in ['baseline','rcc_table','rcc_last']:
 results_list.append(json.loads(run('test_'+name,['build/main_client','build/'+name+'.so'])))
 assert sha(build/'main_client')==client_sha
vendor=json.loads((root/'evidence/audit/VENDOR_SHA256.json').read_text())
assert all(sha(root/'vendor/rcc_20261021'/p)==h for p,h in vendor.items())
summary={'status':'PASS','api_version':'1.0.0','same_main_binary_sha256':client_sha,'swapped_modules':results_list,'vendor_unchanged':True,'gpu_api_compatibility':'NOT_IMPLEMENTED_NOT_VERIFIED','sanitizers_run':False,'performance_experiments':0}
(results/'COMPATIBILITY.json').write_text(json.dumps(summary,indent=2))
(root/'results/COMPATIBILITY.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
