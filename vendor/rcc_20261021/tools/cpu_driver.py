import sys,subprocess,pathlib,time,json,hashlib,platform,csv,collections,statistics,threading,queue,os
P=pathlib.Path(__file__).resolve().parents[1];os.chdir(P)
def run(name,args,limit):
    start=time.time()
    with open('results/'+name+'.stdout.log','w') as out,open('results/'+name+'.stderr.log','w') as err:
        try:r=subprocess.run(args,stdout=out,stderr=err,timeout=limit);code=r.returncode;status='PASS' if code==0 else 'FAIL'
        except subprocess.TimeoutExpired:code=None;status='TIMEOUT'
    pathlib.Path('results/'+name+'.json').write_text(json.dumps(dict(command=args,seconds=time.time()-start,exit_code=code,status=status),indent=2))
    if code!=0:raise RuntimeError(name+': '+status)
def verify_python():
    manifest={g['name']:g for g in json.loads(pathlib.Path('fixtures/manifest.json').read_text())}
    graphs={}
    for name,g in manifest.items():
        adj=[[] for _ in range(g['n'])]
        for line in pathlib.Path('fixtures',g['file']).read_text().splitlines():
            if not line or line[0] in '#%':continue
            u,v=map(int,line.split());adj[u].append(v)
        graphs[name]=adj
    cache={};arrays=elements=0
    for line in open('results/distances.jsonl'):
        row=json.loads(line);key=(row['graph'],row['source'])
        if key not in cache:
            adj=graphs[key[0]];d=[-1]*len(adj);d[key[1]]=0;q=collections.deque([key[1]])
            while q:
                u=q.popleft()
                for v in adj[u]:
                    if d[v]<0:d[v]=d[u]+1;q.append(v)
            cache[key]=d
        assert cache[key]==row['distance'],key
        arrays+=1;elements+=len(row['distance'])
    pathlib.Path('results/python_correctness.json').write_text(json.dumps(dict(status='PASS',arrays=arrays,elements=elements,unique_graph_sources=len(cache)),indent=2))
def gate_summary():
    rows=[]
    for i in range(3):rows+=list(csv.DictReader(open(f'results/gate_{i}.csv')))
    by=collections.defaultdict(dict)
    for r in rows:by[(r['graph'],r['schedule'],r['certificate'],r['mode'])][(r['session'],r['round'])]=float(r['ns'])
    work=collections.defaultdict(lambda:[0,0])
    for r in csv.DictReader(open('results/work.csv')):
        w=work[(r['graph'],r['schedule'],r['mode'])];w[0]+=int(r['edges']);w[1]+=int(r['vertex_tests'])
    out=[]
    controls=['PUSH_N','DO_N','DO_RIE','PUSH_WCC','LAST_RESULT_REUSE']
    for (g,s,c,m),values in by.items():
        strongest=min(controls,key=lambda k:statistics.median(by[(g,s,c,k)].values()))
        for baseline in dict.fromkeys(['PUSH_N','DO_N','DO_RIE',strongest]):
            b=by[(g,s,c,baseline)];ratios=[v/b[k] for k,v in values.items()]
            out.append(dict(graph=g,schedule=s,certificate=c,mode=m,baseline=baseline,strongest_non_rcc=strongest,median_ns=statistics.median(values.values()),median_paired_ratio=statistics.median(ratios),min_ratio=min(ratios),max_ratio=max(ratios),wins=sum(r<1 for r in ratios),pairs=len(ratios),edge_savings=work[(g,s,baseline)][0]-work[(g,s,m)][0],vertex_test_savings=work[(g,s,baseline)][1]-work[(g,s,m)][1],work_condition='cold_only'))
    with open('CPU_INCREMENTAL_VALUE.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    lookup={(r['graph'],r['schedule'],r['certificate'],r['mode'],r['baseline']):r for r in out}
    candidates=['DO_N','DO_RIE','PUSH_RCC_LAST','PUSH_RCC_TABLE','DO_RIE_RCC_LAST','DO_RIE_RCC_TABLE']
    allowed=[];decisions=[]
    for g in sorted({k[0] for k in by}):
        for m in candidates:
            r=lookup[(g,'original','cold',m,'PUSH_N')]
            passed=r['median_paired_ratio']<.95 and r['wins']>=17
            reason='fixed original cold q32 timing gate'
            if m.startswith('DO_RIE_RCC'):
                x=lookup[(g,'original','cold',m,'DO_RIE')]
                passed=passed and x['median_paired_ratio']<.95 and x['wins']>=17 and (x['edge_savings']>0 or x['vertex_test_savings']>0)
                reason+='; incremental time and work vs DO_RIE'
            if passed:allowed.append(g+' '+m)
            decisions.append(dict(graph=g,mode=m,eligible=passed,reason=reason))
    pathlib.Path('config/service_modes.txt').write_text('\n'.join(allowed)+'\n')
    pathlib.Path('results/gate_decisions.json').write_text(json.dumps(decisions,indent=2))
    return len(rows),len(allowed)
def benchmark():
    assert not pathlib.Path('results/BENCHMARK_STARTED.json').exists(),'no automatic retry'
    pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','include','frozen','fixtures','config') for p in pathlib.Path(folder).rglob('*') if p.is_file()}
    pins['build/experiment']=hashlib.sha256(pathlib.Path('build/experiment').read_bytes()).hexdigest()
    pathlib.Path('results/BENCHMARK_STARTED.json').write_text(json.dumps(dict(start=time.time(),pins=pins,rounds=7,processes=3),indent=2))
    procs=[];outputs=[];queues=[];logs=[];start=time.time()
    try:
        for i in range(3):
            log=open(f'results/worker_{i}.stderr.log','w');logs.append(log)
            p=subprocess.Popen(['build/experiment','worker',str(i)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1)
            procs.append(p);q=queue.Queue();queues.append(q)
            def read(pipe,q):
                for line in pipe:q.put(line.strip())
                q.put('EOF')
            threading.Thread(target=read,args=(p.stdout,q),daemon=True).start()
            assert q.get(timeout=60)=='READY'
        for i,p in enumerate(procs):
            p.stdin.write('GATE\n');p.stdin.flush()
            assert queues[i].get(timeout=300)=='GATE_DONE';print('GATE_DONE',i,flush=True)
        n,k=gate_summary();print('GATE_SUMMARY',n,k,flush=True)
        for i,p in enumerate(procs):
            p.stdin.write('SERVICE\n');p.stdin.flush()
            assert queues[i].get(timeout=180)=='SERVICE_DONE';print('SERVICE_DONE',i,flush=True)
        for p in procs:p.stdin.write('QUIT\n');p.stdin.flush()
        for p in procs:assert p.wait(timeout=20)==0
        pathlib.Path('results/BENCHMARK_COMPLETED.json').write_text(json.dumps(dict(status='PASS',seconds=time.time()-start,worker_pids=[p.pid for p in procs],processes=3,rounds=7),indent=2))
    finally:
        for p in procs:
            if p.poll() is None:p.kill();p.wait()
        for f in logs:f.close()
def summarize_service():
    rows=[]
    for i in range(3):rows+=list(csv.DictReader(open(f'results/service_{i}.csv')))
    groups=collections.defaultdict(dict)
    for r in rows:groups[(r['graph'],r['mode'],r['path'],r['q'])][(r['session'],r['round'])]=r
    result=[]
    for (g,m,p,q),v in groups.items():
        b=groups[(g,'PUSH_N','csr',q)]
        ratios=[float(r['total_ns'])/float(b[k]['total_ns']) for k,r in v.items()]
        hist=[(float(r['total_ns'])+float(r['historical_prepare_ns']))/float(b[k]['total_ns']) for k,r in v.items()]
        out=dict(graph=g,mode=m,path=p,q=q,pairs=len(v),median_paired_ratio=statistics.median(ratios),history_inclusive_ratio=statistics.median(hist),wins=sum(x<1 for x in ratios),min_ratio=min(ratios),max_ratio=max(ratios))
        for col in ('total_ns','a_compute_ns','a_completion_ns','b_ready_ns','historical_prepare_ns','validation_ns','release_ns','payload_upper_bytes'):
            out['median_'+col]=statistics.median(float(r[col]) for r in v.values())
        out['b_ready_before_a_count']=sum(int(r['b_ready_before_a']) for r in v.values())
        result.append(out)
    with open('CPU_COLD_WARM_SERVICE.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print('SERVICE_SUMMARY',len(rows),len(result))
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='build_test':
        run('compile_cpu',['g++','-std=c++20','-O2','-pthread','-Wall','-Wextra','-Ifrozen/consumer','-Ifrozen/bridge','-Iinclude','src/experiment.cpp','frozen/consumer/consumers.cpp','-o','build/experiment'],180)
        run('correctness_cpu',['build/experiment','test'],180)
        verify_python()
        run('compiler_version',['g++','--version'],10)
        pathlib.Path('results/environment.json').write_text(json.dumps(dict(platform=platform.platform(),cpu=open('/proc/cpuinfo').read(),python=sys.version),indent=2))
    elif cmd=='benchmark':benchmark();summarize_service()
    elif cmd=='summarize':gate_summary();summarize_service()
    else:raise ValueError(cmd)
