"""Frozen-MAIN, CPU-only DistanceGuard API experiment. No MAIN build commands."""
from pathlib import Path
import hashlib,json,os,platform,subprocess,sys,time
from run_old_p2_service import protected_snapshot,vendor_check
from audit_scope_distance import intake_check,old_checkpoint,verify_arrays
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/dg_api_20261021'
BUILD=ROOT/'build/dg_api_20261021'
os.chdir(ROOT)
PIN_MAIN='d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
def run(name,args,timeout=240):
    start=time.monotonic()
    try:r=subprocess.run(args,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired as e:
        (OUT/(name+'.stdout.log')).write_bytes(e.stdout or b'');(OUT/(name+'.stderr.log')).write_bytes(e.stderr or b'')
        save(name+'.command.json',dict(argv=args,timeout=True,seconds=time.monotonic()-start));raise
    (OUT/(name+'.stdout.log')).write_bytes(r.stdout);(OUT/(name+'.stderr.log')).write_bytes(r.stderr)
    save(name+'.command.json',dict(argv=args,returncode=r.returncode,seconds=time.monotonic()-start))
    assert r.returncode==0,name+' failed; logs preserved'
    return r.stdout.decode()
def frozen():
    paths=[ROOT/'build'/p for p in ('main_client','libgraph.so','baseline.so','rcc_table.so','rcc_last.so')]
    paths += [ROOT.parent/'main/build'/p for p in ('main_client','libgraph.so')]
    paths += [ROOT/p for p in ('api/rcc/v1.hpp','src/cpu_module.cpp','tests/main_client.cpp')]
    for p in (ROOT/'build/main_client',ROOT.parent/'main/build/main_client'):assert sha(p)==PIN_MAIN
    return {str(p):sha(p) for p in paths}
def previous():
    manifest=ROOT/'results/scope_distance_audit_20261021/ARTIFACT_SHA256.json'
    m=json.loads(manifest.read_text());commit='5c489f154d4c7c0bb587972ee307fcaf03a313e2'
    for p,v in m['files'].items():
        raw=subprocess.check_output(['git','--git-dir='+str(ROOT.parent/'main/.git'),'show',commit+':'+p])
        assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256']
        if p.startswith(('results/','research/','intake/','tools/')):assert sha(ROOT/p)==v['sha256']
    return dict(commit=commit,manifest_sha256=sha(manifest),files=len(m['files']),old=old_checkpoint())
def pins():
    paths=list((ROOT/'research').glob('dg_api*'))+[ROOT/'research/DG_API_PROTOCOL.json',Path(__file__)]
    paths+=list(BUILD.glob('*'))
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths) if p.is_file()}
def compile_all():
    common=['g++','-std=c++20','-O2','-Wall','-Wextra','-pthread','-Iapi','-Iresearch','-Ivendor/rcc_20261021/frozen/bridge','-Ivendor/rcc_20261021/frozen/consumer']
    run('compile_core',common+['-fPIC','-c','research/dg_api_module.cpp','-o',str(BUILD/'core.o')])
    run('compile_consumer',common+['-fPIC','-c','vendor/rcc_20261021/frozen/consumer/consumers.cpp','-o',str(BUILD/'consumer.o')])
    for policy in range(11):
        for deferred in range(2):
            for phase in range(2):
                name=f'p{policy}_{deferred}'+('_phase' if phase else '')
                run('compile_'+name,common+['-shared','-fPIC','-DDG_POLICY='+str(policy),'-DDG_DEFERRED='+str(deferred),'-DDG_TIMERS='+str(phase),'research/dg_api_factory.cpp',str(BUILD/'core.o'),str(BUILD/'consumer.o'),'-o',str(BUILD/(name+'.so'))])
    run('compile_service',common+['research/dg_api_service.cpp','-Lbuild','-lgraph','-ldl','-Wl,-rpath,$ORIGIN/..','-o',str(BUILD/'service')])
def prepare():
    OUT.mkdir(exist_ok=False,parents=True);BUILD.mkdir(exist_ok=False,parents=True)
    save('PROTECTED_BEFORE.json',protected_snapshot());save('FROZEN_BEFORE.json',frozen());save('PREVIOUS_BEFORE.json',previous())
    assert intake_check()==92 and vendor_check()==37
    compile_all();reg=[]
    for name,file in [('baseline','build/baseline.so'),('table','build/rcc_table.so'),('last','build/rcc_last.so')]+[(f'DG{p}_{d}',str(BUILD/f'p{p}_{d}.so')) for p in range(6,10) for d in range(2)]:
        r=json.loads(run('main_swap_'+name,[str(ROOT/'build/main_client'),str(Path(file).resolve())]));assert r['status']=='PASS';reg.append(dict(module=name,binary_sha256=PIN_MAIN,result=r))
    save('MAIN_SWAPS.json',dict(status='PASS',unchanged_main_sha256=PIN_MAIN,swaps=reg))
    save('EXTENDED_CONTRACT.json',json.loads(run('extended_contract',[str(BUILD/'service'),'contract'])))
    save('DIAGNOSE.json',json.loads(run('diagnose',[str(BUILD/'service'),'diagnose',str(OUT)])))
    save('PYTHON_ARRAYS.json',verify_arrays([OUT/'arrays.jsonl']))
    save('ENVIRONMENT.json',dict(platform=platform.platform(),python=sys.version,cpuinfo=Path('/proc/cpuinfo').read_text(),compiler=run('compiler_version',['g++','--version']),sessions_sequential=True,GPU_runs=0,paid_resources=0))
    save('PINS.json',pins());assert frozen()==json.loads((OUT/'FROZEN_BEFORE.json').read_text());print('PREPARE_PASS',flush=True)
def benchmark():
    assert not (OUT/'BENCHMARK_STARTED.json').exists(),'fixed campaign cannot be restarted'
    assert pins()==json.loads((OUT/'PINS.json').read_text())
    protocol=json.loads((ROOT/'research/DG_API_PROTOCOL.json').read_text());save('BENCHMARK_STARTED.json',dict(unix=time.time(),protocol=protocol,pins=pins()))
    workers=[]
    for session in range(5):
        r=json.loads(run('worker_'+str(session),[str(BUILD/'service'),'worker',str(session),str(OUT/f'service_{session}.csv')],protocol['worker_timeout_seconds']))
        assert r['status']=='PASS' and r['trials']==5376 and r['arrays']==112896
        workers.append(r);print('WORKER_PASS',session,flush=True)
    phase=json.loads(run('phase',[str(BUILD/'service'),'phase','0',str(OUT/'phases.csv')],240));assert phase['status']=='PASS'
    assert pins()==json.loads((OUT/'PINS.json').read_text())
    after=protected_snapshot();save('PROTECTED_AFTER.json',after);assert after==json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
    assert frozen()==json.loads((OUT/'FROZEN_BEFORE.json').read_text());save('FROZEN_AFTER.json',frozen())
    assert previous()==json.loads((OUT/'PREVIOUS_BEFORE.json').read_text());save('PREVIOUS_AFTER.json',previous())
    save('BENCHMARK_COMPLETED.json',dict(status='PASS',workers=workers,trials=26880,full_arrays=564480,phase=phase,intake_files_verified=intake_check(),vendor_files_verified=vendor_check(),MAIN_unchanged=True,GPU_runs=0,paid_resources=0));print('CAMPAIGN_PASS',flush=True)
if __name__=='__main__':
    {'prepare':prepare,'benchmark':benchmark,'compile':compile_all}[sys.argv[1]]()
