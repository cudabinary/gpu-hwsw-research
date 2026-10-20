"""Independent CPU-only intake audit, replay, matched owned-output experiment."""
from pathlib import Path
from collections import deque,defaultdict,Counter
import csv
import hashlib
import json
import math
import os
import platform
import statistics as stats
import subprocess
import sys
import time
from run_old_p2_service import protected_snapshot,vendor_check

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'intake/rcc_scope_distance_20261021/package/RCC_SCOPE_CPU_MODULE_20261021'
OUT=ROOT/'results/scope_distance_audit_20261021'
BUILD=ROOT/'build/scope_distance_audit_20261021'
os.chdir(ROOT)

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def readcsv(p):
    with p.open() as f:return list(csv.DictReader(f))
def run(name,args,timeout=180):
    started=time.monotonic()
    try:r=subprocess.run(args,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired as e:
        (OUT/(name+'.stdout.log')).write_bytes(e.stdout or b'')
        (OUT/(name+'.stderr.log')).write_bytes(e.stderr or b'')
        save(name+'.command.json',dict(argv=args,timeout=True,seconds=time.monotonic()-started))
        raise
    (OUT/(name+'.stdout.log')).write_bytes(r.stdout)
    (OUT/(name+'.stderr.log')).write_bytes(r.stderr)
    save(name+'.command.json',dict(argv=args,returncode=r.returncode,seconds=time.monotonic()-started))
    assert r.returncode==0, name+' failed; logs preserved, no automatic retry'
    return r.stdout.decode()
def intake_check():
    manifest=json.loads((PACKAGE/'MANIFEST.json').read_text())
    assert all(sha(PACKAGE/i['path'])==i['sha256'] and (PACKAGE/i['path']).stat().st_size==i['bytes'] for i in manifest)
    assert sha(PACKAGE.parent.parent/'original.zip')=='c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c'
    return len(manifest)
def pins():
    paths=[ROOT/'research/scope_distance_audit.cpp',ROOT/'research/SCOPE_DISTANCE_PROTOCOL.json',Path(__file__),BUILD/'matched',BUILD/'scope_probe',BUILD/'distance_probe',ROOT/'api/rcc/v1.hpp']
    paths.extend(p for p in (ROOT/'vendor/rcc_20261021').rglob('*') if p.is_file())
    paths.extend(p for p in PACKAGE.rglob('*') if p.is_file())
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
def old_checkpoint():
    old=ROOT/'results/old_p2_service_20261021/ARTIFACT_SHA256.json'
    m=json.loads(old.read_text())
    parent='1a79b1048cc639c3c23f1000373c3ed6e10bbf7c'
    for p,v in m['files'].items():
        data=subprocess.check_output(['git','--git-dir='+str(ROOT.parent/'main/.git'),'show',parent+':'+p])
        assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256']
        if p.startswith(('results/','research/')) or p in ('tools/run_old_p2_service.py','tools/audit_old_p2_service.py'):
            assert sha(ROOT/p)==v['sha256'] and (ROOT/p).stat().st_size==v['bytes']
    return dict(commit=parent,manifest_sha256=sha(old),files=len(m['files']))
def bfs(a,s):
    d=[-1]*len(a);d[s]=0;q=deque([s])
    while q:
        u=q.popleft()
        for v in a[u]:
            if d[v]<0:d[v]=d[u]+1;q.append(v)
    return d
def verify_arrays(paths):
    adj={};cache={};result=[]
    for p in paths:
        arrays=elements=0
        for line in p.open():
            r=json.loads(line);file=r['file'];source=r['source'];n=r['n']
            if file not in adj:
                a=[[]for _ in range(n)]
                for edge in (PACKAGE/'fixtures'/file).read_text().splitlines():
                    if not edge or edge[0] in '#%':continue
                    u,v=map(int,edge.split());assert 0<=u<n and 0<=v<n;a[u].append(v)
                adj[file]=a
            if (file,source) not in cache:cache[(file,source)]=bfs(adj[file],source)
            assert r['distance']==cache[(file,source)], (file,source,r['mode'])
            arrays+=1;elements+=n
        result.append(dict(file=str(p.relative_to(ROOT)),arrays=arrays,elements=elements))
    return dict(status='PASS',files=result,distinct_graph_source_oracles=len(cache),graph_files=len(adj))
def finite_proofs():
    triangle=closure=frontier=0
    for mask in range(512):
        a=[[]for _ in range(3)]
        for i in range(9):
            if mask>>i&1:a[i//3].append(i%3)
        distances=[bfs(a,s) for s in range(3)]
        for r in range(3):
            for s in range(3):
                if distances[r][s]<0:continue
                for v in range(3):
                    if distances[s][v]>=0:
                        assert distances[r][v]>=0;closure+=1
                        assert distances[r][v]<=distances[r][s]+distances[s][v];triangle+=1
                for level in range(3):
                    layer=[u for u in range(3) if distances[s][u]==level]
                    if not layer:continue
                    horizon=1+max(distances[r][u] for u in layer)
                    for u in layer:
                        for v in a[u]:assert distances[r][v]<=horizon;frontier+=1
    examples=json.loads((PACKAGE/'results/COUNTEREXAMPLES.json').read_text())
    assert len(examples)==4
    assert 2 not in {0,1} and (1,2) in {(0,1),(1,2)}
    a=[[1],[2],[]];inside={1,2}
    assert sum(len(a[u]) for u in inside)==1 and sum(v in inside for row in a for v in row)==2
    e=examples[2];a=[[]for _ in range(9)]
    for u,v in e['edges']:a[u].append(v)
    dr,ds=bfs(a,0),bfs(a,5);layer=[u for u in range(9) if ds[u]==1]
    assert dr[8]>1+min(dr[u] for u in layer) and dr[8]<=1+max(dr[u] for u in layer)
    assert bfs([[1],[2],[3],[]],0)[3]==3
    return dict(status='PASS',graphs=512,closure_checks=closure,triangle_checks=triangle,frontier_edge_checks=frontier,negative_rules_falsified=4)
def replay_work():
    new=readcsv(OUT/'matched/work.csv')
    lookup={(r['graph'],r['schedule'],r['mode'],r['query']):r for r in new}
    mapping={'PUSH_N':'PUSH_N','PUSH_RCC_TABLE':'PUSH_RCC_TABLE','DO_RIE':'DO_RIE','DO_RIE_RCC_TABLE':'DO_RIE_RCC_TABLE','DO_COMPACT':'DO_COMPACT','DO_CLOSURE_COUNT':'SCOPE_COUNT','DO_SCOPE_GLOBAL':'SCOPE_GLOBAL','DO_SCOPE_LOCAL':'SCOPE_LOCAL','DO_SCOPE_COMPACT':'SCOPE_COMPACT','DO_WCC_LOCAL':'WCC_SCOPE'}
    pairs=0
    for r in readcsv(PACKAGE/'results/work.csv'):
        if r['mode'] not in mapping:continue
        other=lookup[(r['graph'],r['schedule'],mapping[r['mode']],r['query_index'])]
        for field in ('edges','vertex_tests','levels'):assert int(r[field])==int(other[field]), (field,r,other)
        pairs+=1
    mapping={'LAST_COUNT':'DIST_COUNT','LAST_CLOSURE':'DIST_CLOSURE','LAST_RADIUS':'DIST_RADIUS','LAST_FRONTIER':'DIST_FRONTIER','PUSH_N':'PUSH_N','PUSH_RCC_TABLE':'PUSH_RCC_TABLE','DO_RIE':'DO_RIE','DO_RIE_RCC_TABLE':'DO_RIE_RCC_TABLE'}
    for r in readcsv(PACKAGE/'results/guard_work.csv'):
        other=lookup[(r['graph'],r['schedule'],mapping[r['mode']],r['query'])]
        for field in ('edges','vertex_tests','levels'):assert int(r[field])==int(other[field]), (field,r,other)
        pairs+=1
    save('WORK_REPLAY.json',dict(status='PASS',matched_mode_query_rows=pairs,exact_fields=['edges','vertex_tests','levels'],historical_and_local_timings_not_pooled=True))
def prepare():
    OUT.mkdir(parents=True,exist_ok=False);BUILD.mkdir(parents=True,exist_ok=False)
    (OUT/'provided').mkdir();(OUT/'matched').mkdir()
    save('PROTECTED_BEFORE.json',protected_snapshot());save('OLD_P2_BEFORE.json',old_checkpoint())
    intake_check();vendor_check()
    common=['-O2','-Wall','-Wextra','-pthread','-I'+str(PACKAGE/'include'),'-Ivendor/rcc_20261021/frozen/consumer']
    for name in ('scope_probe','distance_probe'):
        run('compile_'+name,['g++','-std=c++17',*common,str(PACKAGE/'src'/(name+'.cpp')),'vendor/rcc_20261021/frozen/consumer/consumers.cpp','-o',str(BUILD/name)])
        result=json.loads(run('test_'+name,[str(BUILD/name),'test']))
        save(name+'_TEST.json',result);print(name,'TEST_PASS',flush=True)
        result=json.loads(run('diagnose_'+name,[str(BUILD/name),'diagnose',str(PACKAGE/'fixtures'),str(OUT/'provided')],240))
        save(name+'_DIAGNOSE.json',result)
    run('compile_matched',['g++','-std=c++20',*common,'research/scope_distance_audit.cpp','vendor/rcc_20261021/frozen/consumer/consumers.cpp','-o',str(BUILD/'matched')])
    save('MATCHED_DIAGNOSE.json',json.loads(run('diagnose_matched',[str(BUILD/'matched'),'diagnose',str(OUT/'matched')],240)))
    result=verify_arrays([PACKAGE/'results/arrays.jsonl',PACKAGE/'results/guard_arrays.jsonl',OUT/'provided/arrays.jsonl',OUT/'provided/guard_arrays.jsonl',OUT/'matched/arrays.jsonl'])
    save('PYTHON_ARRAYS.json',result);save('FINITE_PROOFS.json',finite_proofs());replay_work()
    assert json.loads((OUT/'scope_probe_TEST.json').read_text())['mode_query_comparisons']==416768
    assert json.loads((OUT/'distance_probe_TEST.json').read_text())['mode_query_comparisons']==51200
    assert json.loads((OUT/'MATCHED_DIAGNOSE.json').read_text())['full_arrays']==12672
    run('api_regression',['python3','tools/verify.py'],240)
    save('API_COMPATIBILITY.json',json.loads((ROOT/'results/COMPATIBILITY.json').read_text()))
    run('compiler_version',['g++','--version'])
    finalize_prepare()
def finalize_prepare():
    assert not (OUT/'BENCHMARK_STARTED.json').exists()
    for file in ('PYTHON_ARRAYS.json','FINITE_PROOFS.json','WORK_REPLAY.json','API_COMPATIBILITY.json'):
        assert json.loads((OUT/file).read_text())['status']=='PASS'
    assert intake_check()==92 and vendor_check()==37
    head=subprocess.check_output(['git','--git-dir='+str(ROOT.parent/'main/.git'),'rev-parse','refs/heads/research/rcc']).decode().strip()
    save('ENVIRONMENT.json',dict(platform=platform.platform(),python=sys.version,cpuinfo=Path('/proc/cpuinfo').read_text(),source_parent_commit=head))
    save('OLD_P2_BEFORE.json',old_checkpoint())
    save('PINS.json',pins());print('PREPARE_PASS',flush=True)
def benchmark():
    protocol=json.loads((ROOT/'research/SCOPE_DISTANCE_PROTOCOL.json').read_text())
    assert not (OUT/'BENCHMARK_STARTED.json').exists(), 'no automatic benchmark retry'
    assert pins()==json.loads((OUT/'PINS.json').read_text())
    assert json.loads((OUT/'API_COMPATIBILITY.json').read_text())['status']=='PASS'
    save('BENCHMARK_STARTED.json',dict(start_unix=time.time(),protocol=protocol,pins=pins()))
    started=time.monotonic();workers=[]
    for i in range(3):
        r=json.loads(run('worker_'+str(i),[str(BUILD/'matched'),'worker',str(i),str(OUT/('service_'+str(i)+'.csv'))],protocol['worker_timeout_seconds']))
        assert r['status']=='PASS' and r['trials']==8960 and r['arrays']==188160
        workers.append(r);print('WORKER_PASS',i,flush=True)
    assert pins()==json.loads((OUT/'PINS.json').read_text())
    after=protected_snapshot();save('PROTECTED_AFTER.json',after)
    assert after==json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
    assert old_checkpoint()==json.loads((OUT/'OLD_P2_BEFORE.json').read_text())
    save('BENCHMARK_COMPLETED.json',dict(status='PASS',seconds=time.monotonic()-started,workers=workers,trials=26880,full_arrays=564480,intake_files_verified=intake_check(),vendor_files_verified=vendor_check(),MAIN_and_old_P2_preserved=True,GPU_runs=0,paid_resources=0))

if __name__=='__main__':
    {'prepare':prepare,'finalize_prepare':finalize_prepare,'benchmark':benchmark}[sys.argv[1]]()
