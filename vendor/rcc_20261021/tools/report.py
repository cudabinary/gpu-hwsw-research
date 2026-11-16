from pathlib import Path
import csv,json,hashlib,collections,statistics,shutil,gzip,zipfile,io,os
P=Path(__file__).resolve().parents[1]
H=P/'input/handoff/extracted/RCC_CONSUMER_NEXT_CODEX_HANDOFF_202610IFF'.replace('202610IFF','20261021')
def read(p):return json.loads((P/p).read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader((P/p).open(encoding='utf-8-sig')))
def write(name,text):(P/name).write_text(text.strip()+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def original_path(s):
    if os.name=='nt' and s.startswith('/mnt/') and s[6:7]=='/':return Path(s[5].upper()+':/'+s[7:])
    return Path(s)
def save_csv(path,data):
    if not data:return
    with (P/path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def md_table(data,keys):
    return '| '+' | '.join(keys)+' |\n|'+'|'.join('---' for _ in keys)+'|\n'+'\n'.join('| '+' | '.join(str(r[k]) for k in keys)+' |' for r in data)
def fmt(x):return f'{float(x):.4f}'
def main():
    inc=rows('CPU_INCREMENTAL_VALUE.csv');service=rows('CPU_COLD_WARM_SERVICE.csv');work=rows('results/work.csv')
    # Independently compare the handoff's recorded work against this new run.
    bridge=list(csv.DictReader((H/'independent_bridge/results/bridge_work.csv').open()))
    mapping={'PUSH_N':'PUSH_N','PUSH_RCC_TABLE':'PUSH_RCC_TABLE','DO_N':'DO_N','DO_RIE':'DO_RIE','DO_RIE_RCC_LAST':'DO_RIE_RCC_LAST','DO_RIE_RCC_TABLE':'DO_RIE_RCC_TABLE','DO_RIE_TABLE_OFF':'DO_RIE_TABLE_OFF','DO_N_RCC_TABLE':'DO_RCC_TABLE','DO_N_TABLE_OFF':'DO_TABLE_OFF'}
    original={(r['graph'],r['schedule'],r['mode'],r['query_index']):r for r in bridge}
    comparisons=0;differences=[]
    for r in work:
        if r['schedule']=='new_nodup' or r['mode'] not in mapping:continue
        old=original[(r['graph'],r['schedule'],mapping[r['mode']],r['query'])]
        for col,newcol in [('edges','edges'),('seen','seen'),('vertex_tests','vertex_tests'),('publish_visits','table_scan'),('publish_writes','table_write')]:
            comparisons+=1
            if int(old[col])!=int(r[newcol]):differences.append(dict(graph=r['graph'],schedule=r['schedule'],mode=r['mode'],query=r['query'],field=col,old=old[col],new=r[newcol]))
    audit=dict(fields_compared=comparisons,differences=differences,status='MATCH' if not differences else 'DISAGREEMENT')
    write('audit/BRIDGE_RAW_RECONCILIATION.json',json.dumps(audit,indent=2))
    # Revalidate archived exported arrays using the already independently checked
    # current exported arrays indexed by immutable fixture identity and source.
    newarrays={}
    for line in (P/'results/distances.jsonl').open():
        r=json.loads(line);newarrays[(r['graph'],r['source'])]=r['distance']
    archived=0
    with gzip.open(H/'independent_bridge/results/bridge_arrays.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line)
            d=r.get('distance',r.get('distances',r.get('dist')))
            if d is None:raise RuntimeError('archived array schema '+str(list(r)))
            assert d==newarrays[(r['graph'],r['source'])]
            archived+=1
    write('audit/BRIDGE_EXPORTED_ARRAY_RECHECK.json',json.dumps(dict(status='PASS',arrays=archived,method='Archived full arrays compared to new arrays independently verified by Python deque'),indent=2))
    (P/'reference').mkdir(exist_ok=True)
    # The translated handoff documents are shipped in reference/.
    # The original attachments remain under input/handoff.
    for f in ('bridge_work.csv','bridge_arrays.jsonl.gz','test.json','ENVIRONMENT_AND_PROTOCOL.json'):
        shutil.copyfile(H/'independent_bridge/results'/f,P/'reference'/f)
    # All original files read during development and every benchmark pin survive.
    preservation=[]
    prior=P.parent/'TCSC_CONSUMER_FIRST_CPU_20261021'
    candidates=list(prior.glob('*SHA*'))
    for man in candidates:
        if not man.is_file():continue
        try:lines=man.read_text(encoding='utf-8-sig').splitlines()
        except UnicodeError:continue
        for line in lines:
            parts=line.split(None,1)
            if len(parts)!=2 or len(parts[0])!=64:continue
            digest,rel=parts;rel=rel.strip().lstrip('*');q=(prior/rel).resolve()
            assert q.is_relative_to(prior.resolve()) and sha(q)==digest,(rel,'original altered')
            preservation.append(str(q))
    for r in read('audit/INPUT_FREEZE.json')['original_files']:assert sha(Path(r['path']))==r['sha256']
    pins=read('results/BENCHMARK_STARTED.json')['pins']
    for rel,d in pins.items():assert sha(P/rel)==d,('benchmark source changed',rel)
    for r in read('audit/GPU_GUARD_PROVENANCE.json'):assert sha(Path(r['original']))==r['original_sha256']
    driver=read('audit/NATIVE_DRIVER_PROVENANCE.json');assert sha(original_path(driver['path']))==driver['sha256']
    write('audit/PRESERVATION.json',json.dumps(dict(status='PASS',original_manifest_files=len(preservation),benchmark_pins=len(pins),original_paths=preservation),ensure_ascii=False,indent=2))
    # Work and memory ledger: graph / schedule / mode, not invented GPU throughput.
    groups=collections.defaultdict(list)
    for r in work:groups[(r['graph'],r['schedule'],r['mode'])].append(r)
    ledger=[]
    for (g,s,m),v in groups.items():
        x=dict(graph=g,schedule=s,mode=m,requests=len(v))
        for col in ('edges','vertex_tests','levels','rows','bitmap_clear','bitmap_set','table_scan','table_write','stop_checks','output_copy','reuse_hits'):x[col]=sum(int(r[col]) for r in v)
        for col in ('cache_payload','workspace_payload','graph_payload','reverse_payload'):x[col]=max(int(r[col]) for r in v)
        x['payload_condition']='cold sequence; LAST pins existing owned result; process RSS separate'
        ledger.append(x)
    save_csv('WORK_AND_MEMORY_LEDGER.csv',ledger)
    # True paired ratios to strongest measured non-RCC service path, per q and
    # declared availability of a prior reverse, not an executable oracle policy.
    raw=[]
    for i in range(3):raw+=rows(f'results/service_{i}.csv')
    sr=collections.defaultdict(dict)
    for r in raw:sr[(r['graph'],r['q'],r['mode'],r['path'])][(r['session'],r['round'])]=r
    strong=[]
    for key,v in sr.items():
        g,q,m,path=key
        controls=[k for k in sr if k[:2]==(g,q) and 'RCC' not in k[2] and k[3]!='ready']
        best=min(controls,key=lambda k:statistics.median(float(r['total_ns']) for r in sr[k].values()))
        ratios=[float(r['total_ns'])/float(sr[best][pair]['total_ns']) for pair,r in v.items()]
        strong.append(dict(graph=g,q=q,mode=m,path=path,strongest_measured_cold_non_RCC=best[2]+'/'+best[3],paired_ratio=statistics.median(ratios),wins=sum(x<1 for x in ratios),pairs=len(ratios),note='Ready reverse has prior cost; not a cold competitor without adding it'))
    save_csv('CPU_STRONG_SERVICE_COMPARISON.csv',strong)
    gpu=read('results/GPU_PILOT/RECEIPT.json')
    telemetry=read('results/GPU_PILOT/TELEMETRY.json')
    gpurows=[]
    for c in gpu['completed']:
        for r in c['results']:
            if r['kind']=='BFS':gpurows.append(dict(graph=c['case']['fixture'],**r))
    save_csv('GPU_PILOT_RESULTS.csv',gpurows)
    gs=dict(status=gpu['status'],processes=gpu['processes'],completed_BFS=gpu['BFS'],cancelled_requests=gpu['cancellations'],seconds=gpu['seconds'],min_free_MiB=min(t['free_MiB'] for t in telemetry),max_temp_C=max(t['temperature_C'] for t in telemetry),max_device_payload_bytes=max(r['device_payload_bytes'] for r in gpurows),kernel_launches=sum(r['kernel_launches'] for c in gpu['completed'] for r in c['results']),samples=len(telemetry))
    write('results/GPU_SUMMARY.json',json.dumps(gs,indent=2))
    cj=read('results/correctness.json');py=read('results/python_correctness.json')
    rss=[read(f'results/worker_{i}.json')['rss_peak_kib'] for i in range(3)]
    bench=read('results/BENCHMARK_COMPLETED.json')
    lji=[r for r in inc if r['graph']=='livejournal_sampled_4096' and r['schedule']=='original' and r['certificate']=='cold' and r['baseline']=='PUSH_N' and r['mode'] in ('OLD_P0','OLD_P2','DO_N','DO_RIE','PUSH_RCC_TABLE','DO_RIE_RCC_TABLE')]
    ljtable=md_table([dict(mode=r['mode'],ratio=fmt(r['median_paired_ratio']),wins=r['wins']+'/21',edges_saved=r['edge_savings']) for r in lji],['mode','ratio','wins','edges_saved'])
    ljs=[r for r in service if r['graph']=='livejournal_sampled_4096' and r['q']=='32']
    lstable=md_table([dict(mode=r['mode'],path=r['path'],ratio=fmt(r['median_paired_ratio']),history_inclusive=fmt(r['history_inclusive_ratio']),wins=r['wins']+'/21') for r in ljs],['mode','path','ratio','history_inclusive','wins'])
    def bestrow(g,mode,path,q='32'):
        return next(r for r in service if (r['graph'],r['mode'],r['path'],r['q'])==(g,mode,path,q))
    push=bestrow('livejournal_sampled_4096','PUSH_RCC_TABLE','csr')
    do=bestrow('livejournal_sampled_4096','DO_RIE','deferred')
    combine=next(r for r in inc if (r['graph'],r['schedule'],r['certificate'],r['mode'],r['baseline'])==('livejournal_sampled_4096','original','cold','DO_RIE_RCC_TABLE','DO_RIE'))
    write('README_FIRST_KO.md',f"""
# RCC and RIE consumer integration — CPU results and native GPU pilot

The decision was **selective CONTINUE_SW**. Direction+RIE and Push+RCC without a reverse index performed well under different cost conditions. On LiveJournal, RCC skipped zero additional checks after RIE, so the combined path was kept out of the service. The study used the existing node, head, and link representation and builders. It added no partial index or hardware engine.

- The CPU tests passed {cj['comparisons']:,} full-distance comparisons and {cj['assertions']:,} assertions. They included 576 small graphs and 15,147 fixture requests.
- Independent Python checks passed for {py['arrays']:,} arrays and {py['elements']:,} elements. The analysis also checked {archived} historical bridge arrays.
- The CPU campaign used a fixed three processes and seven rounds, yielding 19,278 resident rows and 4,305 service rows. Thresholds were fixed at alpha=15 and beta=24.
- On an RTX 4060 Ti, {gs['processes']} processes passed {gs['completed_BFS']} full-distance BFS runs and {gs['cancelled_requests']} cancellation checks in {gs['seconds']:.2f} seconds. Minimum observed free VRAM was {gs['min_free_MiB']:,} MiB and peak temperature was {gs['max_temp_C']}°C.
- The GPU pilot launched {gs['kernel_launches']} kernels. Static PTX and cubin builds and native owner linking passed. Nsight and sanitizer runs totaled zero.

For the original LiveJournal input at q32, CPU service time including A, preparation, and result delivery was {float(push['median_paired_ratio']):.4f} times Push+EARLY_N for Push+RCC_TABLE and {float(do['median_paired_ratio']):.4f} times Push+EARLY_N for sequential reverse construction followed by Direction+RIE. A resident reverse index changes which options are available. Retain the preparation cost when comparing cold paths. The GPU pilot checked correctness. Repeated GPU speed, 1% interference, and the need for hardware remain open.

Start with [the implementation](MERGED_CONSUMER_IMPLEMENTATION.md), [correctness and lifetime](CERTIFICATE_CORRECTNESS_AND_LIFETIME.md), [baseline reconciliation](SOURCE_BASELINE_RECONCILIATION.md), [cost analysis](COST_AND_INTERFERENCE_ANALYSIS.md), and [the decision](FINAL_DECISION.md). The original bundle contains `CPU_INCREMENTAL_VALUE.csv`, `CPU_COLD_WARM_SERVICE.csv`, `CPU_STRONG_SERVICE_COMPARISON.csv`, and the raw `results/`. The ZIP was retained locally at this checkpoint.
""")
    write('MERGED_CONSUMER_IMPLEMENTATION.md',"""
# Integrated consumer implementation

The three pinned sources for the graph, reverse builder, and P0/P2 under `frozen/consumer` match the originals. The original `frozen/bridge/stop_bridge.hpp` was also preserved. For Direction traversal, the adapter in `include/adapter.hpp` uses the audited bridge logic for exact remaining indegree, the bitmap, and thresholds alpha=15 and beta=24. Push preserves FIFO order and stops at a safe row boundary once the distinct discovery count reaches n or a valid prior certificate bound.

The 17 comparison modes were OLD_P0, OLD_P2, PUSH_N, DO_N, DO_RIE, PUSH_RCC_LAST, PUSH_RCC_TABLE, DO_RIE_RCC_LAST, DO_RIE_RCC_TABLE, PUSH_TABLE_OFF, DO_RIE_TABLE_OFF, PUSH_LAST_OFF, DO_RIE_LAST_OFF, PUSH_WCC, LAST_RESULT_REUSE, DO_N_RCC_TABLE, and DO_N_TABLE_OFF. OFF modes pay the same TABLE or LAST maintenance cost and disable its stopping condition. WCC applies the supplied union-find method to the same graph, paying for a complete CSR scan and `12n` bytes for parent, size, and bound arrays.

The new contract returns a complete distance array as `shared_ptr<const Output>`. The array remains valid after the next request or executor destruction. LAST retains ownership of the result, and TABLE scans the completed `distance[n]` array. The original bridge's LAST result borrowed a scratch buffer valid until the next call. Only LAST_RESULT_REUSE can return the same immutable result directly for a repeated source. It accounts for memory and aliases separately.

Early termination skips the remaining rows or levels and their checks. Direction still needs the complete reverse index and pays for count, scan, and scatter. Push+RCC requires no reverse index and avoids building and storing it. Savings already supplied by RIE are counted only once.
""")
    write('CERTIFICATE_CORRECTNESS_AND_LIFETIME.md',"""
# Correctness, certificates, and lifetime

The contract is a complete shortest-distance array for an immutable, directed, unweighted multigraph. Duplicate edges and self-loops are preserved. The stopping conditions cover distances. Counting all shortest paths, emitting edge callbacks, preserving visitation order, and weighted graphs are outside this contract.

For RCC, if `s ∈ R` for a previously completed BFS's reachable set `R`, then `Reach(s) ⊆ R`. Once the exact discovered count reaches a valid bound `|R|`, no further reachable vertices remain. `TABLE[v]` stores the minimum size among completed sets containing `v`. LAST uses only the most recent completed result. The public API provides no way to inject an oracle reachability count as a bound.

For RIE, `remaining` is the exact sum of indegrees of undiscovered vertices. When it reaches zero, no incoming edge can lead to an undiscovered vertex. EARLY_N and RIE are sufficient conditions derived from existing metadata. Their academic priority remains outside the claim.

The Direction frontier queue holds the current frontier. TABLE updates read only the completed distance array. Incomplete runs, cancellations, and output allocation failures preserve the previous valid certificate and publish no new output or certificate. Owned output allocation finishes before TABLE updates, which then run without allocation. When the cache budget is insufficient or allocation failure is injected, execution falls back to exact PUSH_N or DO_RIE. Reverse indexes from a different graph object are rejected even when the numeric version matches. Use a new executor for graph changes. Concurrent mutation of the CSR is unsupported.

One owner thread mutates an executor. Concurrent cache writers and lock-free publication are outside the contract. The original Catalog's mutex, epoch, and shared-ownership reverse-index contract still applies. Owned immutable outputs and graph ownership keep readers valid. Small exhaustive and randomized checks compared the actual reachability count and the bound for every source. Tests covered cancellation, restart, invalid sources, graph identity, cache and output allocation failures, and readers that outlive the executor. This checkpoint did not run sanitizers.

The GPU owner uses a single stream and reads counters after the level completes. Only a successful `atomicCAS` adds a newly discovered vertex to the distinct count and, when statistics are enabled, adds its exact indegree to the level's discovered indegree total. Kernel completion on that stream is the publication boundary. GPU Push stops at level boundaries, while the CPU can stop at row boundaries. Both return the same shortest distances, and the amount of work avoided may differ. GPU TABLE updates use the completed host array. There is no device-side shared certificate queue.
""")
    write('SOURCE_BASELINE_RECONCILIATION.md',f"""
# Source and bridge reconciliation

After the external download failed, the study used a local attachment with the same name and size. The 7,431,945-byte ZIP had SHA-256 `b2c6f4d49d0af97e11125c1588e444f85e6255ecf1b54a165ba4920d004b963b`. CRC, path traversal, duplicate name, and link checks passed. The 73-file outer manifest and the nested ZIP manifests were rechecked. `audit/INPUT_FREEZE.json` records the hashes and check counts for each nested ZIP.

The three vendored consumer sources match the local originals byte for byte. The original {len(preservation)}-file manifest and {len(pins)} benchmark pins were rechecked at completion. Earlier Consumer-first ratios on LiveJournal q32 were 0.840713 sequential and 0.865155 concurrent. Those results retain their own scope, with different PUSH_N, owned-output, and certificate-publication assumptions from the new study.

The comparison checked {comparisons:,} fields across nine common modes and 18 graph and schedule combinations against historical bridge records. There were {len(differences)} mismatches. The new full arrays validated in Python also matched {archived} historical exports. The 87,552 historical cases came from prior C++ runs and are reported separately from the new checks.

Limits and contractual differences:

- The bridge Push field `levels=0` means uninstrumented. New Push counts expanded rows and levels.
- The original bridge LAST returned a scratch or buffer reference valid until the next call. The new module pays to return an independently owned complete array.
- The bridge cache lacked budget and allocation-failure fallback. The new adapter adds them.
- Original RCC Direction uses a different definition of `remaining` from Codex's exact indegree sum. Treat their timings as distinct backends.
- The original and holdout schedules had already been seen. One new order was fixed in advance with seed `20261021`.
- Relabeling the original schedule follows the vertex map. A numeric source in the holdout need not name the corresponding relabeled vertex.
- The supplied EPYC/g++ 14.2 timings and the new i5-14500/WSL/g++ 15.2 timings come from different environments.

The initial ZIP reader paused while looking for duplicate README names after the import and CRC checks had completed. The three required documents were read in order using their exact paths. This tooling issue is outside the experiment's success and failure counts.
""")
    write('COST_AND_INTERFERENCE_ANALYSIS.md',f"""
# Cost and interference in the CPU measurements

Three independent workers ran sequentially, with seven rounds each. Total time was {bench['seconds']:.2f} seconds, with zero retries, threshold tuning runs, and warmups. Diagnostic counters and uninstrumented timing used separate template instantiations. Peak worker RSS was {rss} KiB. This includes all preloaded fixtures, reference results, and reverse indexes.

## Resident consumer on the original LiveJournal input, 33 requests

Ratios use PUSH_N as the baseline. q32 consists of one initial request and 32 follow-ups. The reverse index is resident. Cold certificate timing starts with executor initialization and certificate construction. Warm timing starts after three prior requests, whose cost is recorded as `priming_ns`. Graph, reverse index, and workspace setup are outside the resident window. The window includes copying new results, updating certificates, constructing caches, and destroying the executor. Validation and result release have separate fields, `validation_ns` and `release_ns`.

{ljtable}

The median paired DO_RIE_RCC_TABLE / DO_RIE ratio was {float(combine['median_paired_ratio']):.6f}. RCC saved zero additional edge checks and zero vertex checks. Timing variation close to parity provides no evidence of an incremental benefit.

## Measured q32 service

A uses the frozen `plan_a`. A completion includes copying A's result and the count and scan used to build a certificate. A compute and completion have separate raw CSV fields. Total time includes the builder's count, scan, cursor, scatter, and verification, synchronization and joins, and workspace allocation. Ready paths record historical reverse-build time separately and include a sum with that history. That sum combines measured components. Input parsing and independent CPU validation are outside the compute window. CPU build time remains a CPU measurement.

{lstable}

Push+RCC performed well at cold q32 without a reverse index. With a prebuilt reverse index, compare against the ready Direction+RIE path. The measured sequential path beat concurrent preparation. The experiment did not implement an online policy with advance knowledge of q. `CPU_STRONG_SERVICE_COMPARISON.csv` pairs each result against the strongest observed non-RCC service path at the same q. This is a retrospective reporting baseline.

## Memory and excluded costs

Graph and reverse each use `8(n+1)+4m` bytes. Full builder peak is `24n+8+4m`. Push workspace uses `8n`, Direction `12n+8ceil(n/64)`, TABLE `4n`, and WCC `12n`. Owned results use `4n` per unique result. LAST retains ownership of a result. `LAST_RESULT_REUSE` aliases are counted once.

The conservative service payload bound assumes all results overlap the full builder peak. All cases fit within 32 MiB. Allocator headers, control blocks, and thread stacks are outside the formula and included in process RSS.

The service total ends when results are available. Caller release happens later, and final teardown of service owners and builders was not fully instrumented. Fine-grained differences and equivalence within 1% remain untested.
""")
    write('NEGATIVE_CONTROLS_AND_FAILURES.md',"""
# Negative results, failures, and limitations

The raw records retain timing outliers and losses. The resident consumer and service each have 21 pairs. Statistical significance, noninferiority, and 1% interference were outside this evidence. The new source order was fixed before seeing results. The original and holdout orders were already known. The service ran only the predefined original schedule, leaving generality across other full-service schedules unknown.

The combined path was dropped where RCC avoided zero additional checks after RIE on LiveJournal and its relabeling. Large RCC gains on disconnected synthetic SCCs are specific to those inputs. WCC can supply the same size bound in some synthetic cases. The controls expose the costs of WCC preprocessing and TABLE initialization and updates, as well as simple repeated-source reuse via LAST_RESULT_REUSE. DO_RIE_RCC passed no fixture's full predefined service gate.

CPU and CUDA builds and correctness runs succeeded. The CPU compiler emitted one line-layout warning involving two independent `if` statements. The measured source and executable stayed fixed after measurement. The CPU suite and GPU pilot passed. Sanitizers were outside this checkpoint.

The following issues occurred before the GPU pilot.

- The first GPU engine counter sample returned an error. Execution paused before any CUDA launch.
- An additional sandbox diagnostic could not access the counter object. A separate native diagnostic confirmed 806 NVIDIA samples with status 0. The original error's root cause remained undetermined, and the failing sample was discarded.
- Windows PowerShell 5 policy prevented file-based execution. The run used the existing PowerShell 7 installation with the system policy intact.
- PID 1944 was a protected DWM process, so native modules could not be inspected. The monitor used its previously approved exact PID, name, and creation identity.
- The copied monitor lost fractional seconds when reparsing PowerShell 7 JSON `DateTime` objects. Comparing those objects directly in UTC corrected the issue. The matching tolerance and the VRAM, temperature, and watchdog limits stayed fixed.

There was one actual kernel pilot campaign. Normal GUI contexts were monitored using exact PID, creation time, modules, and GPU engine. Protected OS contexts were monitored using pinned CIM identity and engine activity. GUI shader activity could still occur, so the measured environment differs from a dedicated headless system.
""")
    write('NOVELTY_SCOPE.md',"""
# Novelty and the hardware question

Direction-optimizing BFS, EARLY_N, containment between completed reachable sets, WCC bounds, and result caching apply or combine existing software methods. The exact metadata supports a proof of the RIE stopping condition. Academic priority needs separate review. New hardware, a novel GPU runtime algorithm, and a novel partial index remain unestablished.

An effective reverse-index consumer and inexpensive termination certificates can skip measurable work. Any hardware comparison must account for required output writes of n elements, additional reverse reads and construction, GPU atomics, and host synchronization at level boundaries. The results did not establish a need for a dedicated Shadow Engine.

On the GPU, RIE used already collected statistics to skip the final unnecessary level, and Push+RCC skipped levels using a prior completed result. These observations do not identify the dominant SM, L2, or DRAM constraint or establish that new hardware beats strong software. The decision is CONTINUE_SW. The hardware question remains open.
""")
    write('CUDA_HOST_HARNESS_READINESS.md',f"""
# CUDA owner, harness, and execution status

`cuda/owner.cpp` loads inputs, builds the reverse index with the frozen CPU builder, allocates and transfers GPU buffers, drives BFS one level at a time, compares results, and cleans up. The native Windows Driver API header comes from a previously validated copy. PTX and cubin builds for `sm_89`, native Windows cross-linking, and Linux/Windows ABI checks passed. GPU `View` is 112 bytes and `Counter` is 24 bytes.

The modes are 0 (PUSH_N), 1 (PUSH_RCC_TABLE), 2 (DO_N), and 3 (DO_RIE). These cover the two promising candidates and their strong controls. The GPU omitted Direction+RCC because RIE already covered the observed savings. The pilot verified resident-consumer correctness with a CPU-built reverse index. A GPU reverse builder and the concurrent end-to-end Plan A service were outside its scope. GPU Push stops at level boundaries, so CPU row-boundary performance cannot predict it directly.

The GPU oracle is a complete host deque-BFS distance array. A historical result reader was also rechecked. Output copies and host TABLE publication were recorded separately. `stream_interval_ms` includes host submission and synchronization between CUDA events. The one-shot raw `wall_ms` includes cold module and OS effects and is unsuitable for a performance conclusion.

The owner reads exact new discovery counts and remaining-indegree decrements after stream completion. Incomplete and cancelled results leave TABLE unchanged, and the next source starts a new traversal. The graph is immutable for the owner's lifetime. A numeric version alone cannot validate an external reverse index. Guards cover device count at most n, source and edge bounds, 32 MiB of allocations, epoch wraparound, 128 levels, and 2,040 dispatches. A CUDA error puts the owner in a failed state and subsequent queries are rejected.

The pilot passed {gs['completed_BFS']} BFS runs and {gs['cancelled_requests']} cancellations across {gs['processes']} processes and {gs['kernel_launches']} kernel launches. Total time was {gs['seconds']:.3f} seconds and peak experiment-owned device payload was {gs['max_device_payload_bytes']:,} bytes. Across {gs['samples']} telemetry samples, the minimum free VRAM was {gs['min_free_MiB']:,} MiB and peak temperature was {gs['max_temp_C']}°C. Each child recorded explicit synchronization and context release, and its PID disappeared from SMI. Native module and engine monitors used a three-second freshness window, a 20-second child watchdog, and a 300-second total dispatch limit. The watchdog cannot guarantee immediate preemption of a running kernel. Bounded inputs, loops, and launches reduce that risk.
""")
    write('GPU_MINIMAL_APPROVAL_REQUEST.md',f"""
# Completed, separately authorized GPU correctness pilot

The work began with a CPU and static-build scope. The user later explicitly authorized the bounded GPU pilot recorded here. Earlier F/P1/P2 permits remained inactive. The execution manifest, `config/GPU_MINIMAL_PILOT.json`, retains the source, binary, input, and monitor hashes.

- The pilot checked whether EARLY_N, RIE, and RCC preserve complete distance arrays under GPU level publication and source switching.
- Inputs were micro7 (duplicates, self-loop, disconnected component, and sink), LiveJournal4096, and synthetic scc4_d32.
- The four modes per input were PUSH_N, PUSH_RCC_TABLE, DO_N, and DO_RIE, for 12 processes.
- Each process ran three complete BFS traversals, including the initial certificate setup where applicable, and one explicit cancellation. The total was 36 BFS runs plus 12 cancellations, or 48 calls.
- Limits were 300 seconds overall, 20 seconds per child, 32 MiB of workspace, at least 2,048 MiB free VRAM at startup and 1,536 MiB while running, and temperature below 78°C.
- The run used zero warmups, retries, Nsight Systems or Compute sessions, sanitizer runs, installations, external downloads, and paid GPU jobs.
- The pilot stopped further dispatch on a graphics PID outside the pinned allowlist, ambiguous or stale telemetry, a CUDA error, a distance mismatch, a watchdog trigger, or a VRAM or temperature violation.
- Further GPU execution required confirmed context release.

All 12 processes passed in {gs['seconds']:.2f} seconds. Candidate next steps were uninstrumented, paired consumer measurements with the same owner and a separate experiment for the end-to-end GPU service. The pilot included an intermediate cancellation check, CPU reverse construction, and host validation. Its measured scope was correctness. The campaign ended after completing the bounded CPU measurements and GPU pilot.
""")
    write('FINAL_DECISION.md',f"""
# Final decision at this checkpoint — selective CONTINUE_SW

1. **Direction+RIE reduced cost under the tested baseline.** On the original LiveJournal input, the median paired resident DO_RIE / PUSH_N ratio was about 0.759. Sequential DO_RIE at q32 took {float(do['median_paired_ratio']):.4f} times as long with preparation included. The result is specific to the tested graph and schedule. Sequential preparation beat concurrent preparation in this comparison.
2. **RCC's incremental savings depend on the consumer.** On LiveJournal, RCC saved zero additional edge or vertex checks after RIE, so the combined path was dropped. On disconnected SCC graphs, RCC can reduce work after Direction+RIE. Push+RCC and WCC provide stronger controls and alternative explanations there. In Push without a reverse index, an earlier reachability bound can skip rows beyond what EARLY_N certifies. Even when the reachable set is only slightly smaller than n, this can avoid processing a large last row or level. The effect depends on source changes, row order, and stopping boundaries and uses existing hardware.
3. **The lowest total cost depends on reverse-index availability.** Cold Push+RCC_TABLE at q32 took {float(push['median_paired_ratio']):.4f} times as long as PUSH_N and avoided reverse construction. A fully resident reverse index makes ready DO_RIE another strong option. `CPU_COLD_WARM_SERVICE.csv` records q0, q1, q2, and q8 separately. The measured non-RCC baseline comparison includes WCC and simple result reuse.

A completed BFS can eliminate later rows or levels in a subsequent search under this contract. RCC adds no savings for work already eliminated by RIE. In some conditions, avoiding reverse construction is less expensive. This checkpoint did not establish a need for a new builder, partial index, or hardware engine.

The CPU showed practical improvements for specific inputs, schedules, and q values. Independent novelty and the need for hardware remain open. The historical GPU passed 36 BFS runs and 12 cancellations. GPU performance, Plan A interference of at most 1%, and full-service q32 improvement are **UNKNOWN**. Establishing speedup requires repeated performance measurements.
""")
    write('REPRODUCE.md',"""
# Reproducing the earlier consumer study

Keep the original snapshot read-only and run in a new copy. The historical CPU environment had WSL, Python 3, g++ 15.2 with C++20, and pthreads. Those installed tools were sufficient without network access.

```text
python3 tools/cpu_driver.py build_test
python3 tools/cpu_driver.py benchmark
```

To rerun from a distribution ZIP containing earlier results, copy the code, `frozen`, `fixtures`, and `config/PROTOCOL.json` into a clean directory and create empty `results`, `build`, and `audit` directories. The benchmark rejects a workspace containing `BENCHMARK_STARTED.json`. It starts exactly three persistent CPU workers. Each waits after GATE and then executes SERVICE within the same process once the predefined rules finalize `service_modes`. Keep the original parameters.

Raw CPU outputs are `results/gate_0..2.csv`, `results/service_0..2.csv`, `results/work.csv`, and `distances.jsonl`. The resident batch contains 33 requests, with the three historical requests that prime the warm certificate recorded separately. The service uses the original schedule at q0, q1, q2, q8, and q32 and records historical ready reverse-build cost separately.

```text
/usr/local/cuda-13.3/bin/nvcc -std=c++17 -O2 -arch=sm_89 -Icuda --cubin cuda/kernels.cu -o build/rcc_kernels.cubin
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static -Icuda -Ifrozen/consumer -I/usr/local/cuda-13.3/include cuda/owner.cpp -o build/rcc_owner.exe
```

These commands compile and link without launching GPU work. The executable's `--abi` and `--cpu-check` modes do not load the driver. An actual GPU launch used the pilot wrapper with current authorization, a fresh exact PID baseline, all relevant pins, continuous monitoring, and a new run directory. `tools/gpu_pilot.py` refuses to rerun in an existing results directory. Historical baselines, PIDs, and tokens apply only to the original pilot.

`results/GPU_PILOT` holds the original GPU results, commands, raw telemetry, and confirmation of driver context release. Static-build output is under `results/gpu_static_*` and `results/gpu_abi_*`. `tools/report.py` audits and aggregates in a workspace containing the original supplied files under `input/handoff`. The distribution ZIP omits duplicate input archives. Provide the original attachments read-only at that location for full report regeneration. Core CPU reproduction does not need them.
""")
    write('audit/PREFLIGHT_EVENTS.md',"""
# Diagnostics before GPU dispatch

`results/gpu_preflight/native.xml/result.json` records the first telemetry probe, with zero CUDA children. `counter_diagnostic.json` records a read-only sandbox diagnostic that could not find the counter object. The native read-only repeat in `counter_native_diagnostic.json` recorded 806 NVIDIA samples with status 0. Policy prevented Windows PowerShell 5 from starting with `-File`. The diagnostic used the installed PowerShell 7 with the OS policy unchanged.

The native process guard could not inspect modules for protected DWM PID 1944. The approved baseline for PID 1944, `dwm.exe`, and creation time `2026-10-18T21:18:40.650692Z` was checked against the current CIM identity. The first adapter lost fractional seconds when reparsing PowerShell 7 JSON DateTime values. The corrected copy converts those values directly to UTC before exact comparison. Normal processes outside the protected DWM and OS brokers must pass native module inspection.

These issues preceded GPU dispatch and occurred with zero CUDA kernels launched. One GPU_PILOT then ran with the pinned baseline and updated pins. All 12 processes passed. There were no failures, retries, limit relaxations, or unrelated process terminations during the run.
""")
    summary=dict(cpu_correctness=cj,python=py,bridge=audit,archive_arrays=archived,gpu=gs,benchmark=bench,preservation_files=len(preservation),rss_peak_kib=rss,local_zip_only=True)
    write('results/FINAL_SUMMARY.json',json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('bridge','benchmark')},ensure_ascii=False))
if __name__=='__main__':main()
