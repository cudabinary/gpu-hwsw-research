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
    for f in ('README_FIRST_KO.md','MERGE_REVIEW_KO.md','CODEX_WORK_ORDER_KO.txt'):
        shutil.copyfile(H/f,P/'reference'/('HANDOFF_'+f))
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
# RCC / RIE Consumer 통합 — CPU 결과와 실제 GPU 파일럿

이번 결론은 **선택적 CONTINUE_SW**다. Direction+RIE와 reverse 없는 Push+RCC는 서로 다른 비용 조건에서 유효하다.
LiveJournal에서 RIE 뒤 RCC의 추가 검사 생략은 **0**이므로 결합 경로는 서비스에 연결하지 않았다.
Node/head/link, 부분 인덱스, builder, HW 엔진을 새로 만들지 않았다.

- 새 CPU: {cj['comparisons']:,} 전체 거리 비교, {cj['assertions']:,} assertions PASS. 소형 그래프 576개, fixture 요청 15,147개 포함.
- 새 독립 Python: {py['arrays']:,} 배열 / {py['elements']:,} 원소 PASS. 기존 bridge 증거 배열 {archived}개도 대조했다.
- CPU: 고정 3개 프로세스 × 7회; resident 행 19,278개, 서비스 행 4,305개. 임계값 alpha=15, beta=24 고정.
- 실제 RTX 4060 Ti: {gs['processes']}개 프로세스, 전체 거리 BFS {gs['completed_BFS']}회와 취소 {gs['cancelled_requests']}회 PASS.
  {gs['seconds']:.2f}초, 관측 여유 VRAM 최소 {gs['min_free_MiB']}MiB, 최고 {gs['max_temp_C']}°C.
- GPU 커널 {gs['kernel_launches']}회. 정적 PTX/cubin 및 native owner 링크 PASS. Nsight·sanitizer 0회.

CPU LiveJournal original q32의 A+준비+반환 포함 서비스는 Push+RCC_TABLE {float(push['median_paired_ratio']):.4f}배,
순차 reverse+Direction+RIE {float(do['median_paired_ratio']):.4f}배 (각각 강한 Push+EARLY_N 대비).
resident reverse가 이미 있으면 Direction+RIE가 다른 선택이 된다. 준비 비용을 지워서 순위를 비교하지 않는다.
GPU 파일럿은 반복 성능 실험이 아니며 GPU 성능 성공·1% 간섭·HW 필요성을 입증하지 않는다.

읽는 순서: MERGED_CONSUMER_IMPLEMENTATION → CERTIFICATE_CORRECTNESS_AND_LIFETIME →
SOURCE_BASELINE_RECONCILIATION → COST_AND_INTERFERENCE_ANALYSIS → FINAL_DECISION.
CPU_INCREMENTAL_VALUE.csv, CPU_COLD_WARM_SERVICE.csv, CPU_STRONG_SERVICE_COMPARISON.csv와 results/에 원시 기록이 있다.
이 ZIP은 로컬 제출물이다. 외부 업로드를 수행하지 않았다.
""")
    write('MERGED_CONSUMER_IMPLEMENTATION.md',"""
# 실제 통합 구현

`frozen/consumer`의 Graph, reverse Builder, P0/P2 소스 3개는 원본과 동일하다.
`frozen/bridge/stop_bridge.hpp`도 보존했다. 새 `include/adapter.hpp`는 Direction 실행에
감사한 bridge의 정확한 remaining-indegree / bitmap / alpha=15, beta=24 코드를 사용한다.
Push는 FIFO를 유지하며 distinct 발견 수가 n 또는 과거 증거 상한에 도달한 후 안전한 행 경계에서 멈춘다.

17개 비교 경로: OLD_P0, OLD_P2, PUSH_N, DO_N, DO_RIE, PUSH_RCC_LAST, PUSH_RCC_TABLE,
DO_RIE_RCC_LAST, DO_RIE_RCC_TABLE, PUSH_TABLE_OFF, DO_RIE_TABLE_OFF, PUSH_LAST_OFF,
DO_RIE_LAST_OFF, PUSH_WCC, LAST_RESULT_REUSE, DO_N_RCC_TABLE, DO_N_TABLE_OFF.
OFF는 같은 TABLE/LAST 유지 작업을 수행하며 RCC 종료에만 쓰지 않는다.
WCC는 제공된 union-find 방법을 동일 그래프에 적용한다. parent/size/bound 12n 바이트와 전체 CSR 스캔을 부담한다.

새 결과 계약은 `shared_ptr<const Output>`이며 전체 거리 배열을 복사해 돌려준다.
다음 실행이나 Executor 파괴 뒤에도 유효하다. LAST는 이 결과의 소유권을 유지하고 TABLE은 완료 distance[n]을 스캔한다.
기존 bridge LAST scratch swap의 다음 호출까지인 borrowed-reference 계약과 구별한다.
LAST_RESULT_REUSE만 같은 source의 불변 결과를 그대로 돌려줄 수 있다. 그 별칭과 메모리를 별도 계수한다.

생략되는 것은 탐색의 남은 행/레벨과 그 검사 비용이다. 최종 reverse가 필요한 Direction에서는
COUNT/scan/scatter를 생략하지 않는다. Push+RCC는 reverse 자체가 필요 없어서 그 전체 구축·보관 비용을 피한다.
RIE가 이미 생략한 작업을 RCC의 기여로 중복 계상하지 않는다.
""")
    write('CERTIFICATE_CORRECTNESS_AND_LIFETIME.md',"""
# 정확성, 증거와 수명

계약은 불변 directed unweighted multigraph의 전체 최단거리 배열이다. 중복 간선과 self-loop를 보존한다.
모든 shortest-path 수, edge callback, 방문 순서, 가중 그래프에는 이 종료 조건을 확장하지 않는다.

RCC: 과거 완료 BFS의 도달 집합 R에서 s∈R이면 Reach(s)⊆R이다.
정확한 발견 수가 유효 상한 |R|에 도달하면 더 발견할 정점이 없다.
TABLE[v]는 v를 포함한 완료 집합 크기의 최솟값이고, LAST는 최근 완료 결과만 사용한다.
oracle의 실제 도달 수를 실행 상한으로 주입하는 공개 API는 없다.
RIE: remaining은 미발견 정점들의 정확한 indegree 합이다.
0이면 미발견 정점으로 들어갈 간선이 없으므로 추가 도달이 불가능하다.
EARLY_N과 RIE는 기존 메타데이터의 충분조건이며 학술적 최초성은 주장하지 않는다.

Direction의 frontier queue는 전체 방문 목록이 아니다. TABLE 갱신은 완료 distance 배열만 읽는다.
미완료·cancel·출력 할당 실패는 새 Output/certificate를 공개하지 않고 이전 유효 인증을 보존한다.
TABLE 갱신 전에 owned output 할당이 완료되며 그 이후 갱신은 할당 없는 루프다.
cache 예산 부족 또는 주입된 할당 실패 시 강한 PUSH_N/DO_RIE로 돌아간다.
같은 숫자 version이라도 다른 Graph 객체의 reverse는 거부한다.
Graph 변경은 새 Executor로 수행한다. mutable CSR의 동시 갱신은 지원하지 않는다.

한 Executor는 한 owner thread만 변경한다. 이 연구는 cache 동시 writer 지원이나 lock-free publication을 주장하지 않는다.
기존 Catalog의 mutex/epoch/shared_ptr reverse 수명 계약은 유지한다.
owned const Output과 graph 소유권이 reader 수명을 보장한다.
소형 전수/무작위 검사에서 모든 source의 실제 도달 수와 상한 부등식을 진단용으로 비교했다.
취소, 재시작, invalid source, graph identity, cache/output allocation 실패, Executor 파괴 후 reader를 검사했다.
sanitizer는 이번에 실행하지 않았으며 기존 sanitizer PASS를 새 코드에 이월하지 않는다.

GPU는 단일 owner stream으로 레벨 완료를 기다린 뒤 counter를 읽는다.
atomicCAS 성공 때만 distinct 수/정확 indegree를 더하며 같은 stream의 kernel 종료가 publication 경계다.
GPU Push는 CPU와 달리 행 중간/행 경계가 아닌 레벨 경계 종료다. 동일한 최소거리 계약이지만 생략량은 다를 수 있다.
GPU TABLE은 host의 완료 배열로만 갱신하며 device-side 공유 certificate queue를 새로 만들지 않았다.
""")
    write('SOURCE_BASELINE_RECONCILIATION.md',f"""
# 원본 / bridge 대조

외부 다운로드가 실패한 뒤 동일 파일명·크기의 로컬 첨부 사본을 사용했다.
실제 7,431,945바이트 ZIP의 SHA-256은 b2c6f4d49d0af97e11125c1588e444f85e6255ecf1b54a165ba4920d004b963b.
CRC 및 경로 탈출/중복 이름/링크 검사를 통과했다. outer manifest 73개와 nested ZIP manifest를 재검사했다.
audit/INPUT_FREEZE.json에 각 nested ZIP의 실제 SHA·검사 개수가 있다.

Consumer 원본 vendor 3개는 로컬 원본과 바이트가 같다. 원본 manifest {len(preservation)}개 파일을 완료 시 재검사했다.
이번 benchmark 당시의 pin {len(pins)}개도 그대로다.
기존 Consumer-first LJ q32 순차 0.840713 / 병행 0.865155 성과를 유지한다.
이번 강한 Push_N baseline, owned output, certificate publication 계약의 결과와 수치를 직접 혼합하지 않는다.

bridge raw 기록과 새 구현의 공통 9개 모드·18개 graph/schedule에서 {comparisons:,}개 필드를 대조했다.
불일치 {len(differences)}개. 별도 Python으로 확인된 새 전체 배열과 기존 export {archived}개도 동일했다.
이는 제공된 과거 C++ 실행을 다시 했다는 뜻은 아니다. 과거 87,552건과 새 검사 건수는 별도다.

확인된 한계/차이:
- bridge Push의 levels=0은 계측 미구현 값이며 실제 0레벨 탐색이 아니다. 새 Push는 expanded rows/실행 level을 계수한다.
- 기존 bridge LAST 반환값은 다음 호출까지의 scratch/buffer 참조다. 새 모듈은 독립 소유 전체 배열 반환 비용을 포함한다.
- bridge cache는 예산/할당 실패 fallback이 없다. 새 adapter에서 추가했다.
- RCC 원본 Direction의 remaining 정의는 Codex의 정확 indegree 합과 다르므로 타이밍을 같은 backend처럼 섞지 않는다.
- original/holdout은 이미 본 일정이다. 새 순서 한 개만 seed=20261021로 사전 고정했다.
- relabel original은 vertex mapping을 따르지만 holdout의 숫자 source는 동일 relabel vertex를 의미하지 않는다.
- 제공된 EPYC/g++14.2 타이밍과 이번 i5-14500/WSL/g++15.2 타이밍은 직접 비율 계산하지 않는다.

최초 ZIP 읽기 도구는 중복 README 검색에서 멈췄지만 import/CRC는 완료돼 있었다.
정확한 root 경로로 요구된 세 문서를 순서대로 읽었다. 이 준비 도구 오류를 실험 실패/성공 건수에 섞지 않는다.
""")
    write('COST_AND_INTERFERENCE_ANALYSIS.md',f"""
# 비용과 간섭 — 새 CPU 실측

3개 독립 worker 프로세스가 순서대로 활성화돼 각각 7회 측정했다.
동시에 3개 benchmark를 실행하지 않았다. 총 {bench['seconds']:.2f}초이며 실패/성능 재시도·임계값 튜닝·warmup은 0회다.
진단 계수 코드와 비계측 timing template을 분리했다. 프로세스 RSS 최고값은 {rss}KiB다.
이는 preload된 모든 fixture/정답/역인덱스까지 포함한 프로세스 고수위이며 개별 서비스 payload와 같지 않다.

## Resident consumer, LiveJournal original 33요청

아래 기준은 PUSH_N이다. q32는 첫 요청 1개+후속 32개다. 역인덱스는 resident 상태다.
certificate cold는 Executor 초기화/증거 생성부터, warm은 과거 요청 3개를 수행한 상태부터 잰다.
warm의 priming_ns를 숨기지 않고 원시에 보존한다. graph/reverse/workspace 구성은 resident 측정 경계 밖이다.
모든 새 결과 복사·증거 갱신·cache 생성 및 Executor 파괴는 resident 구간에 포함된다.
검증과 반환된 결과의 해제는 별도 validation_ns/release_ns다.

{ljtable}

DO_RIE_RCC_TABLE / DO_RIE의 짝 중앙값은 {float(combine['median_paired_ratio']):.6f}.
추가 edge/vertex-test 생략은 0/0이다. 1에 가까운 타이밍 흔들림을 추가 알고리즘 효과로 인정하지 않는다.

## 실제 서비스 q32

A는 frozen plan_a 그대로 실행한다. A 이후 결과 복사·증거를 만들기 위한 count/scan도 A completion에 포함한다.
A-compute와 completion은 원시 CSV의 별도 필드다.
builder의 COUNT/scan/cursor/scatter/verify와 동기화/join, 실제 workspace 할당을 총시간에 포함한다.
ready의 역사적 reverse 구축 시간은 service window 밖에 별도 기록하고 history-inclusive 합도 표시한다.
이를 cold wall-clock 실측으로 이름 붙이지 않는다.
입력 파일 parsing/CPU 정답검증은 컴퓨팅 구간 밖이며 GPU 결과에 CPU 구축시간을 GPU 변환시간으로 바꾸지 않는다.

{lstable}

Cold q32에서는 reverse 없는 Push+RCC가 유효하다. 준비된 reverse가 이미 있으면 Direction+RIE의 ready 경로와 따로 비교해야 한다.
병행은 순차보다 빠른 것으로 선택하지 않았다. 미래 q를 아는 온라인 정책을 구현했다는 뜻은 아니다.
CPU_STRONG_SERVICE_COMPARISON.csv는 같은 q에서 관측한 최강 비-RCC 경로와 짝 비교한다.
이는 보고서용 사후 envelope이지 source별 oracle runtime이 아니다.

## 메모리 및 포함하지 않은 비용

Graph = 8(n+1)+4m, reverse = 8(n+1)+4m, full builder peak = 24n+8+4m.
Push workspace=8n, Direction=12n+8ceil(n/64), TABLE=4n, WCC=12n.
owned outputs는 실제 unique 결과마다 4n이고 LAST는 결과를 pin한다. LAST_RESULT_REUSE의 별칭은 중복 할당으로 세지 않는다.
서비스 payload upper는 모든 결과와 full builder peak가 겹친다고 보수적으로 계산하며 모두 32MiB 내다.
allocator header/control block·thread stack은 이 payload 식 밖이며 프로세스 RSS에는 포함된다.
출력 전달 시점과 caller가 훗날 해제하는 시점을 구별한다. 서비스의 owner/builder 최종 객체 파괴를
개별 ns로 전부 계측하지 않았으므로, CSV total은 결과가 사용 가능해지는 latency이지 전체 프로세스 종료비용이 아니다.
이 작은 미계측 teardown을 포함한 미세 차이/1% 동등성은 판정하지 않는다.
""")
    write('NEGATIVE_CONTROLS_AND_FAILURES.md',"""
# 음성 결과와 실패/한계

원시 시간 이상치와 승패를 삭제하지 않았다. consumer와 service는 각각 21개 짝만 있다.
통계적 유의성, 비열등성, 1% 간섭을 선언하지 않는다.
새 source 순서는 결과를 보고 재선택하지 않았고 original/holdout을 새 미지 데이터로 표현하지 않는다.
현재 서비스는 사전 지정 original만 실행했다. 다른 일정의 전체 서비스 일반성은 UNKNOWN이다.

LJ와 relabel의 RIE 이후 RCC 추가 일이 0인 조건은 결합을 중단했다.
단절 SCC 합성의 큰 RCC 이득을 실제 그래프 일반 성능으로 확대하지 않는다.
WCC로 같은 크기 상한을 얻을 수 있는 합성에서는 reachability 정보의 신규성을 주장하지 않는다.
WCC 전처리와 n개 TABLE 초기화/갱신, LAST_RESULT_REUSE로 단순 중복 source 효과를 드러냈다.
DO_RIE_RCC 경로는 어느 fixture에서도 고정 service gate를 모두 통과하지 못했다.

새 CPU/CUDA 컴파일·정확성 실행은 성공했다. CPU 컴파일에는 줄 배치에 관한 warning 한 건이 있으며
두 독립 if문의 의미를 바꾸지 않는다. 성능 측정 후 그 소스를 다시 수정/컴파일하지 않았다.
새 sanitizer는 실행하지 않았다. CPU PASS / GPU 파일럿 PASS / sanitizer 미실행을 구별한다.

GPU 실행 전 실제 문제를 별도 기록했다:
- 최초 GPU 엔진 counter sample 오류로 CUDA launch 0회 상태에서 보류했다.
- 추가 sandbox 진단은 카운터 object 접근에 실패했다. native 권한의 별도 진단에서 NVIDIA sample 806개 status 0을 확인했다.
  최초 오류의 근본 원인은 확정하지 않았다. 오류 sample을 유효하다고 처리하지 않았다.
- Windows PowerShell 5의 File 실행은 정책상 시작되지 않았다. 시스템 정책을 바꾸지 않고 기존 PowerShell 7을 사용했다.
- PID 1944는 보호 DWM이며 native module 접근이 불가능했다. 이전 승인된 정확한 PID/name/creation identity만 재사용했다.
- PowerShell 7 JSON의 DateTime을 다시 Parse하면서 소수초가 소실되는 새 감시 복사본의 호환 문제를 수정했다.
  DateTime 값을 그대로 UTC로 비교하도록 고쳤으며 matching tolerance·VRAM·온도·watchdog 한도를 완화하지 않았다.
이것들은 CUDA 실패 후 재시도가 아니다. 실제 커널 파일럿은 한 캠페인만 수행했다.

일반 GUI 컨텍스트는 고정 PID·생성시각·모듈·GPU engine으로 감시했다.
보호 OS 컨텍스트는 modules 대신 고정 CIM identity와 engine을 감시한 예외다.
따라서 모든 GUI의 셰이더가 전혀 없다고 보장하지 않는다. 측정 GPU 결과를 전용 headless 환경과 동일시하지 않는다.
""")
    write('NOVELTY_SCOPE.md',"""
# 신규성 및 HW 판단

Direction-Optimizing BFS, EARLY_N, 완료 도달 집합의 포함관계, WCC 상한, 결과 캐시는 기존 SW 방법의 적용/조합이다.
RIE의 충분조건은 이 정확한 메타데이터에서 증명됐으나 학술적 최초성은 별도 검토 없이 주장하지 않는다.
새 HW, GPU runtime 신규 알고리즘, 부분 인덱스 신규성은 입증되지 않았다.

실용 결과와 신규성을 구별한다. 유효한 reverse 소비자와 저렴한 종료 인증으로 실제 작업을 생략하는 것은 유용하다.
이 결과는 전용 Shadow Engine/무제한 대역폭/무료 쓰기의 필요성을 보이지 않는다.
필수 결과 n개 원소 반환, 추가 reverse 읽기·구축, GPU atomic/host level synchronization은 실제 비용이다.
GPU의 RIE는 이미 수집하는 통계로 마지막 불필요한 레벨을 생략했고, Push+RCC도 과거 완성 증거로 레벨을 생략했다.
이 관찰만으로 SM/L2/DRAM 중 어느 자원이 지배적인지, 새 HW가 강한 SW보다 빠른지 판정하지 않는다.
현재 근거는 CONTINUE_SW에 해당하며 HW 필요성은 UNKNOWN이다.
""")
    write('CUDA_HOST_HARNESS_READINESS.md',f"""
# CUDA owner / harness 및 실행 상태

`cuda/owner.cpp`는 실제 입력 로드·frozen CPU reverse 구축·GPU 할당/전송·BFS level driver·정답 비교·cleanup을 포함한다.
빈 main이나 링크 전용 stub이 아니다. Windows native Driver API header는 기존 검증된 복사본을 사용했다.
PTX/cubin sm_89, native Windows cross link, Linux/Windows ABI 비교 PASS.
GPU View={112}바이트, Counter={24}바이트다.

실행 모드: 0 PUSH_N, 1 PUSH_RCC_TABLE, 2 DO_N, 3 DO_RIE.
유망 후보 2개와 해당 강한 대조군이다. RIE가 RCC를 흡수한 Direction+RCC는 GPU에 넣지 않았다.
CPU의 reverse builder를 사용한 **resident consumer 정확성 파일럿**이다. GPU reverse builder나 GPU 병행 Plan A 전체 서비스는 실행하지 않았다.
GPU의 Push 종료는 레벨 경계라 CPU 행 경계 성능을 그대로 예측할 수 없다.

GPU oracle은 host deque BFS 전체 배열이며 history reader도 재확인한다.
출력 복사와 host TABLE publication 시간을 별도 기록한다.
stream_interval_ms는 host 제출/동기화 간격을 포함한 CUDA event 간격이며 순수 kernel busy time이 아니다.
원시 pilot wall_ms는 1회 측정이고 cold module/OS 간섭을 포함하므로 성능 최종 판정에 쓰지 않는다.

정확한 신규 발견 counter / remaining indegree 감소를 stream 완료 후 읽는다.
불완전/취소 결과는 TABLE을 갱신하지 않으며 다음 source로 재실행한다.
graph는 owner 수명 동안 immutable; numeric version만으로 외부 reverse를 받아들이지 않는다.
device count≤n, source/edge 범위, 32MiB 할당, epoch wrap, 128레벨/2040 dispatch 경계를 검사한다.
CUDA 오류 후 owner는 실패 상태이며 추가 query를 거부한다.

실제 결과: {gs['completed_BFS']} BFS + {gs['cancelled_requests']} cancellation PASS, {gs['processes']} processes, {gs['kernel_launches']} kernel launches.
전체 {gs['seconds']:.3f}초; 최대 자체 device payload {gs['max_device_payload_bytes']:,}바이트.
telemetry {gs['samples']}개; 최소 free {gs['min_free_MiB']}MiB, 최대 {gs['max_temp_C']}°C.
각 child의 explicit synchronize/context-release marker와 SMI PID 소멸을 확인했다.
Native module/engine monitors, 신선도 3초, 20초 child watchdog, 총300초 dispatch 제한을 유지했다.
watchdog는 이미 실행 중인 단일 GPU kernel을 즉시 선점하는 보장이 아니다. bounded input/loop/launch가 그 위험을 줄인다.
""")
    write('GPU_MINIMAL_APPROVAL_REQUEST.md',f"""
# 최소 GPU 계획 — 최신 사용자 승인으로 실행 완료

최초 요청의 CPU/static 제한 이후 사용자가 이 대화에서 GPU 사용을 명시적으로 승인했다.
승인을 다시 요구하지 않고 다음 한정 파일럿을 수행했다. 과거 F/P1/P2 승인 파일을 재활성화하지 않았다.
실행 manifest는 config/GPU_MINIMAL_PILOT.json이며 원본 소스·바이너리·입력·감시기 SHA pin을 보존한다.

- 질문: EARLY_N/RIE/RCC가 GPU level publication과 source 교대에서도 전체 거리 정확성을 보존하는가?
- 입력: micro7(중복·self-loop·단절·sink), LiveJournal4096, synthetic scc4_d32.
- 각 입력에서 PUSH_N / PUSH_RCC_TABLE / DO_N / DO_RIE, 총12개 프로세스.
- 프로세스마다 완료 BFS 3회(첫 인증 생성 포함)+명시적 취소1회. 총36 BFS+12취소=48 호출.
- 예산: 총300초, child20초, workspace32MiB, 시작 free≥2048MiB, 실행 free≥1536MiB, 관측 온도<78°C.
- warmup0, 자동재시도0, Nsight Systems/Compute0, sanitizer0. 추가 설치/외부 다운로드/유료 GPU0.
- 그래픽 컨텍스트 고정목록 밖 PID, 불명확/오래된 telemetry, CUDA 오류, 거리 mismatch, watchdog/VRAM/온도 위반 시 즉시 중단.
- 종료 후 context 종료가 확인되지 않으면 추가 GPU 실행 금지.

실측 {gs['seconds']:.2f}초, 12/12 PASS. 승인 부재로 남겨진 작업이 아니다.
다음 단계 후보는 same owner의 비계측 paired 소비자 측정과 GPU 전체 서비스 경계의 별도 설계다.
현재 pilot에는 중간 취소 검사·CPU reverse 구축·host validation이 있어 이를 전체 서비스 GPU 가속으로 해석하지 않는다.
이번 연구의 CPU 한정 반복 예산과 파일럿을 완료한 뒤 중단했으며 GPU 성능 캠페인을 무한 확장하지 않았다.
""")
    write('FINAL_DECISION.md',f"""
# 최종 판정: 선택적 CONTINUE_SW

1. **유효한 Direction 성과는 강한 기준선에서도 남는다.**
LJ original의 resident DO_RIE / PUSH_N 짝 중앙값은 약0.759이며,
준비 포함 q32 순차 DO_RIE 서비스는 {float(do['median_paired_ratio']):.4f}배였다.
그래프/일정 전반의 무조건적 우위는 아니다. 순차가 병행보다 유리한 결과를 그대로 유지한다.

2. **RCC의 추가 생략은 소비자에 따라 다르다.**
LJ에서는 RIE 이후 RCC의 추가 edge/vertex-test 생략이 0이다. 결합을 중단했다.
단절 SCC에서는 RCC가 Direction+RIE 이후에도 일을 생략하지만 Push+RCC 및 WCC라는 더 강한 설명/대조가 있다.
reverse 없는 Push에서 RCC는 EARLY_N이 보장하지 못하는 과거 도달 크기 상한으로 추가 행을 생략한다.
LJ의 도달 집합이 n보다 조금 작은 경우에도 마지막 큰 행/레벨을 처리할 필요가 없어질 수 있다.
이는 실제 source 변경/행 순서와 종료 경계에 의존하며 신규 HW를 필요로 하지 않는다.

3. **전체 비용의 승자는 reverse의 가용 상태에 따라 달라진다.**
LJ cold q32 Push+RCC_TABLE은 {float(push['median_paired_ratio']):.4f}배이며 reverse 구축을 피한다.
완전 reverse가 이미 resident라면 ready DO_RIE가 다른 강한 경로다.
q1/q2/q8 및 q0의 비용은 CPU_COLD_WARM_SERVICE.csv에 보존했으며 q32 성과를 임의로 확대하지 않는다.
WCC/단순 결과 재사용 포함 최강 measured 비-RCC 경로와의 비교도 제공한다.

**최종 질문에 대한 답:** 이 계약에서는 미리 수행한 완료 BFS가 다음 탐색의 남은 행/레벨을 실제로 없앨 수 있다.
그러나 RIE로 이미 사라진 일을 RCC가 다시 없앨 수는 없다. 필요한 경우 reverse 자체를 만들지 않는 쪽이 더 저렴하다.
새 builder·부분 인덱스·HW 엔진을 만들 이유는 이 결과에서 나오지 않는다.

CPU 실용 개선: 특정 입력/일정/q에서 확인. 독립 신규성: 미입증. 새 HW 필요성: 미확정.
실제 GPU 정확성: 36 BFS/12취소 PASS. GPU 성능 성공·Plan A 간섭≤1%·GPU q32 전체 개선: UNKNOWN.
이번 GPU 결과는 CPU 근거를 실제 장치의 정확성까지 확장했으며, 반복 계측 없는 가속 결론은 내리지 않는다.
""")
    write('REPRODUCE.md',"""
# 재현법

원본은 읽기 전용으로 보존한다. 새 복사본에서 실행한다.
필수 CPU 도구는 이미 설치된 WSL Python3, g++15.2(C++20), pthread다. 설치/네트워크는 필요 없다.

```text
python3 tools/cpu_driver.py build_test
python3 tools/cpu_driver.py benchmark
```

결과가 존재하는 배포 ZIP에서 재실행하려면 새 디렉터리에 코드·frozen·fixtures·config/PROTOCOL.json만 복사하고
빈 results/build/audit를 만든다. BENCHMARK_STARTED.json이 있는 폴더에서는 재시도를 거부한다.
benchmark는 정확히 3개 persistent CPU 프로세스를 시작한다. 각 프로세스가 GATE 후 기다리고,
사전 규칙으로 service_modes가 확정된 후 같은 프로세스에서 SERVICE를 진행한다.
원본과 다른 파라미터를 시험해 유리한 결과만 고르지 않는다.
CPU 원시 결과: results/gate_0..2.csv, results/service_0..2.csv, results/work.csv, distances.jsonl.
resident 결과는 총33요청, warm history는 과거3요청을 별도 기록한다.
service는 original q0/1/2/8/32이며 ready reverse 역사적 준비 비용을 따로 기록한다.

```text
/usr/local/cuda-13.3/bin/nvcc -std=c++17 -O2 -arch=sm_89 -Icuda --cubin cuda/kernels.cu -o build/rcc_kernels.cubin
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static -Icuda -Ifrozen/consumer -I/usr/local/cuda-13.3/include cuda/owner.cpp -o build/rcc_owner.exe
```

위 두 명령은 정적 컴파일이다. 실행 파일의 --abi / --cpu-check는 driver를 로드하지 않는다.
GPU launch는 raw exe 단독 호출로 진행하지 않는다. 최신 authorization, 새로운 정확한 PID baseline,
모든 pin, 유효 continuous guard, 새 단일 실행 디렉터리가 필요하다.
tools/gpu_pilot.py는 이미 결과 폴더가 있으면 재실행을 거부한다.
이 제출물의 과거 baseline/PID/token을 다른 날짜의 실행 권한으로 재사용하지 않는다.

GPU 결과/명령/원시 telemetry: results/GPU_PILOT. 드라이버 context 종료 확인도 보존했다.
정적 컴파일 출력: results/gpu_static_* / gpu_abi_*.
tools/report.py는 첨부 원본이 input/handoff에 있는 작업 폴더에서 감사/재집계를 한다.
배포 ZIP은 중복 첨부 archive를 제외했으므로 full report 재생성은 원본 첨부를 같은 위치에 읽기 전용으로 제공해야 한다.
핵심 CPU 재현에는 첨부 archive가 필요 없다.
""")
    write('audit/PREFLIGHT_EVENTS.md',"""
# 커널 실행 전 진단 기록

results/gpu_preflight/native.xml/result.json: 첫 telemetry probe, 0 CUDA children.
counter_diagnostic.json: sandbox 범위의 읽기 진단. 카운터 object를 찾지 못했다.
counter_native_diagnostic.json: native 읽기 전용 재진단, NVIDIA 806 sample status=0.
Windows PowerShell 5 -File 시도는 실행 정책 때문에 시작되지 않았다 (tool transcript).
기존 PowerShell 7에서 진단을 수행했으며 OS 실행 정책은 변경하지 않았다.

native process_guard는 보호 DWM PID1944의 module 접근을 거부했다 (tool transcript).
예전 승인 baseline의 PID1944/dwm.exe/2026-10-18T21:18:40.650692Z와 현재 CIM identity를 대조했다.
첫 baseline adapter는 PS7 JSON DateTime을 문자열로 Parse하면서 소수초를 잃어 그 정확한 예외를 인정하지 못했다.
새 복사본에서 DateTime을 그대로 UTC로 바꾸도록 수정하고 다시 정확 비교했다.
protected DWM과 OS brokers 외 일반 PID는 native module 검사를 모두 통과해야 한다.

위 준비 실패들은 GPU process dispatch 이전이며 당시 CUDA kernels=0이다.
그 뒤 frozen baseline+새 pins로 단일 GPU_PILOT을 실행했고 12/12 PASS했다.
실행 중 실패/재시도/한도 완화/다른 프로세스 종료는 0회였다.
""")
    summary=dict(cpu_correctness=cj,python=py,bridge=audit,archive_arrays=archived,gpu=gs,benchmark=bench,preservation_files=len(preservation),rss_peak_kib=rss,local_zip_only=True)
    write('results/FINAL_SUMMARY.json',json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('bridge','benchmark')},ensure_ascii=False))
if __name__=='__main__':main()
