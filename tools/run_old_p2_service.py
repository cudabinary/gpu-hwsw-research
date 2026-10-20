"""Bounded CPU retest. Run prepare, benchmark (once), then analyze in WSL."""
from pathlib import Path
import collections
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/old_p2_service_20261021'
BUILD = ROOT / 'build/old_p2_service_20261021'
os.chdir(ROOT)

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def run(name, args, timeout=120):
    start = time.monotonic()
    r = subprocess.run(args, capture_output=True, timeout=timeout)
    (OUT / (name+'.stdout.log')).write_bytes(r.stdout)
    (OUT / (name+'.stderr.log')).write_bytes(r.stderr)
    record = dict(argv=args, returncode=r.returncode, seconds=time.monotonic()-start)
    save(name+'.command.json', record)
    if r.returncode:
        raise RuntimeError(name+' failed; preserved logs; no automatic retry')
    return r.stdout.decode()

def pins():
    paths = [ROOT/'research/old_p2_service.cpp', ROOT/'research/OLD_P2_PROTOCOL.json', Path(__file__), BUILD/'worker']
    paths += [p for p in (ROOT/'vendor/rcc_20261021').rglob('*') if p.is_file()]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}

def vendor_check():
    expected = json.loads((ROOT/'evidence/audit/VENDOR_SHA256.json').read_text())
    assert all(sha(ROOT/'vendor/rcc_20261021'/p)==h for p,h in expected.items())
    return len(expected)

def protected_snapshot():
    main = ROOT.parent/'main'
    tracked = subprocess.check_output(['git','-C',str(main),'ls-files','-z']).decode().split('\0')
    original = ROOT.parent.parent/'TCSC_RCC_RIE_CPU_STATIC_20261021'
    expected = json.loads((ROOT/'evidence/audit/VENDOR_SHA256.json').read_text())
    return {
        'main_head': subprocess.check_output(['git','-C',str(main),'rev-parse','HEAD']).decode().strip(),
        'main_status': subprocess.check_output(['git','-C',str(main),'status','--porcelain']).decode(),
        'main_tracked_sha256': {p:sha(main/p) for p in tracked if p},
        'original_matching_files_sha256': {p:sha(original/p) for p in expected if (original/p).is_file()},
    }

def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    BUILD.mkdir(parents=True, exist_ok=False)
    save('PROTECTED_BEFORE.json', protected_snapshot())
    vendor_check()
    flags=['g++','-std=c++20','-O2','-Wall','-Wextra','-pthread',
           '-Ivendor/rcc_20261021/include','-Ivendor/rcc_20261021/frozen/bridge','-Ivendor/rcc_20261021/frozen/consumer']
    run('compile',flags+['research/old_p2_service.cpp','vendor/rcc_20261021/frozen/consumer/consumers.cpp','-o',str(BUILD/'worker')],180)
    result=json.loads(run('correctness',[str(BUILD/'worker'),'correctness','0',str(OUT/'distances.jsonl')]))
    manifests=json.loads((ROOT/'vendor/rcc_20261021/fixtures/manifest.json').read_text())
    graphs={}
    for item in manifests:
        if item['name'] not in ('livejournal_sampled_4096','lj_permuted'):
            continue
        path=ROOT/'vendor/rcc_20261021/fixtures'/item['file']
        assert sha(path)==item['sha256']
        adj=[[] for _ in range(item['n'])]
        for line in path.read_text().splitlines():
            if not line or line[0] in '#%': continue
            a,b=map(int,line.split());adj[a].append(b)
        graphs[item['name']]=adj
    cache={}
    arrays=elements=0
    for line in (OUT/'distances.jsonl').read_text().splitlines():
        r=json.loads(line);key=(r['graph'],r['source'])
        if key not in cache:
            adj=graphs[r['graph']];d=[-1]*len(adj);d[r['source']]=0;queue=collections.deque([r['source']])
            while queue:
                u=queue.popleft()
                for v in adj[u]:
                    if d[v]<0: d[v]=d[u]+1;queue.append(v)
            cache[key]=d
        assert r['distance']==cache[key]
        arrays+=1;elements+=len(r['distance'])
    assert arrays==result['arrays']==336
    save('CORRECTNESS.json',dict(status='PASS',arrays=arrays,elements=elements,distinct_graph_sources=len(cache),independent_python_oracle=True))
    run('compiler_version',['g++','--version'])
    save('ENVIRONMENT.json',dict(platform=platform.platform(),python=sys.version,cpuinfo=Path('/proc/cpuinfo').read_text(),protocol=json.loads((ROOT/'research/OLD_P2_PROTOCOL.json').read_text())))
    save('PINS.json',pins())
    print('PREPARE_PASS',arrays,elements,flush=True)

def benchmark():
    assert not (OUT/'BENCHMARK_STARTED.json').exists(), 'single-use benchmark; no retries'
    assert json.loads((OUT/'PINS.json').read_text())==pins(), 'pins changed'
    assert json.loads((OUT/'CORRECTNESS.json').read_text())['status']=='PASS'
    assert json.loads((ROOT/'results/COMPATIBILITY.json').read_text())['status']=='PASS'
    started=time.time()
    save('BENCHMARK_STARTED.json',dict(start_unix=started,processes=3,rounds=7,mirror_sweeps=2,retries=0,warmup=0,pins= pins()))
    workers=[]
    for session in range(3):
        r=json.loads(run('worker_'+str(session),[str(BUILD/'worker'),'worker',str(session),str(OUT/('service_'+str(session)+'.csv'))],60))
        assert r['status']=='PASS' and r['trials']==224 and r['arrays']==4704
        workers.append(r)
        print('WORKER_PASS',session,flush=True)
    assert json.loads((OUT/'PINS.json').read_text())==pins()
    after=protected_snapshot()
    save('PROTECTED_AFTER.json',after)
    assert after==json.loads((OUT/'PROTECTED_BEFORE.json').read_text()), 'protected evidence changed'
    save('BENCHMARK_COMPLETED.json',dict(status='PASS',seconds=time.time()-started,workers=workers,processes=3,rounds=7,trials=672,arrays=14112,vendor_files_verified=vendor_check(),protected_main_and_original_unchanged=True,gpu_runs=0))

def analyze():
    assert json.loads((OUT/'BENCHMARK_COMPLETED.json').read_text())['status']=='PASS'
    rows=[]
    for session in range(3):
        with (OUT/('service_'+str(session)+'.csv')).open() as f: rows+=list(csv.DictReader(f))
    assert len(rows)==672 and sum(int(r['arrays']) for r in rows)==14112
    variants=[('PUSH_N','csr'),('PUSH_RCC_TABLE','csr'),('OLD_P2','deferred'),('OLD_P2','ready')]
    lookup={}
    for r in rows:
        key=tuple(r[k] for k in ('graph','q','session','round','sweep','mode','path'))
        assert key not in lookup
        lookup[key]=r
    def value(r,metric):
        if metric=='history_inclusive_ns': return float(r['total_ns'])+float(r['historical_prepare_ns'])
        return float(r[metric])
    summary=[];noise=[]
    for graph in ('livejournal_sampled_4096','lj_permuted'):
        for q in ('8','32'):
            for a in variants:
                same=[lookup[(graph,q,str(s),str(b),str(w),*a)] for s in range(3) for b in range(7) for w in range(2)]
                null=[value(lookup[(graph,q,str(s),str(b),'1',*a)],'total_ns')/value(lookup[(graph,q,str(s),str(b),'0',*a)],'total_ns') for s in range(3) for b in range(7)]
                noise.append(dict(graph=graph,q=int(q),mode=a[0],path=a[1],mirror_ratio_median=stats.median(null),min_ratio=min(null),max_ratio=max(null),session_medians=[stats.median(null[s*7:(s+1)*7]) for s in range(3)]))
                for b in variants:
                    if a==b:continue
                    for metric in ('total_ns','history_inclusive_ns','cleanup_window_ns','lifecycle_ns'):
                        blocks=[]
                        for s in range(3):
                            for round_ in range(7):
                                ratios=[value(lookup[(graph,q,str(s),str(round_),str(w),*a)],metric)/value(lookup[(graph,q,str(s),str(round_),str(w),*b)],metric) for w in range(2)]
                                blocks.append(math.sqrt(ratios[0]*ratios[1]))
                        sessions=[stats.median(blocks[s*7:(s+1)*7]) for s in range(3)]
                        median=stats.median(blocks);wins=sum(x<1 for x in blocks)
                        summary.append(dict(graph=graph,q=int(q),candidate='/'.join(a),baseline='/'.join(b),metric=metric,primary_blocks=21,sessions=3,median_paired_ratio=median,wins=wins,min_ratio=min(blocks),max_ratio=max(blocks),session_medians=sessions,guarded_advantage=median<.95 and wins>=17 and all(x<.95 for x in sessions),median_candidate_ns=stats.median(value(r,metric) for r in same)))
    save('COMPARISONS.json',summary)
    save('NOISE_CONTROLS.json',noise)
    save('ANALYSIS.json',dict(status='PASS',trials=len(rows),arrays=14112,distance_elements=14112*4096,primary_blocks_per_comparison=21,sessions=3,mirror_sweeps_independent=False,comparisons=len(summary),prior_results_pooled=False,api_adapter_performance='NOT_MEASURED',gpu_api_compatibility='NOT_VERIFIED',new_algorithm_or_novelty_claim=False))
    for r in summary:
        if r['candidate']=='PUSH_RCC_TABLE/csr' and r['metric'] in ('total_ns','lifecycle_ns'):
            print(json.dumps(r))

if __name__=='__main__':
    {'prepare':prepare,'benchmark':benchmark,'analyze':analyze}[sys.argv[1]]()
