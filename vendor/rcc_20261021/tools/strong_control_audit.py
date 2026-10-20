"""Reaggregate existing measurements only. Never starts a benchmark."""
from pathlib import Path
import csv,json,collections,statistics,shutil
P=Path(__file__).resolve().parents[1]
def rows(p):return list(csv.DictReader((P/p).open(encoding='utf-8-sig')))
def save(p,data):
    with (P/p).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
by=collections.defaultdict(dict)
for session in range(3):
    for r in rows(f'results/gate_{session}.csv'):
        by[(r['graph'],r['schedule'],r['certificate'],r['mode'])][(r['session'],r['round'])]=float(r['ns'])
work=collections.defaultdict(lambda:[0,0])
for r in rows('results/work.csv'):
    x=work[(r['graph'],r['schedule'],r['mode'])];x[0]+=int(r['edges']);x[1]+=int(r['vertex_tests'])
controls=['OLD_P0','OLD_P2','PUSH_N','DO_N','DO_RIE','PUSH_WCC','LAST_RESULT_REUSE']
out=[]
for (g,s,c,m),v in by.items():
    strongest=min(controls,key=lambda x:statistics.median(by[(g,s,c,x)].values()))
    for baseline in dict.fromkeys(['PUSH_N','DO_N','DO_RIE',strongest]):
        b=by[(g,s,c,baseline)];ratios=[value/b[pair] for pair,value in v.items()]
        out.append(dict(graph=g,schedule=s,certificate=c,mode=m,baseline=baseline,strongest_non_rcc=strongest,median_ns=statistics.median(v.values()),median_paired_ratio=statistics.median(ratios),min_ratio=min(ratios),max_ratio=max(ratios),wins=sum(x<1 for x in ratios),pairs=len(ratios),edge_savings=work[(g,s,baseline)][0]-work[(g,s,m)][0] if c=='cold' else 'UNKNOWN',vertex_test_savings=work[(g,s,baseline)][1]-work[(g,s,m)][1] if c=='cold' else 'UNKNOWN',work_condition='cold_measured' if c=='cold' else 'warm_work_not_measured'))
old=P/'results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv'
if not old.exists():shutil.copyfile(P/'CPU_INCREMENTAL_VALUE.csv',old)
save('CPU_INCREMENTAL_VALUE.csv',out)
lj=next(r for r in out if (r['graph'],r['schedule'],r['certificate'],r['mode'],r['baseline'])==('livejournal_sampled_4096','original','cold','DO_RIE','OLD_P2'))
service=[]
for session in range(3):service+=rows(f'results/service_{session}.csv')
sg=collections.defaultdict(dict)
for r in service:sg[(r['graph'],r['mode'],r['path'],r['q'])][(r['session'],r['round'])]=r
a=[]
for (g,m,path,q),v in sg.items():
    b=sg[(g,'PUSH_N','csr',q)]
    for col in ('a_compute_ns','a_completion_ns'):
        values=[float(r[col])/float(b[pair][col]) for pair,r in v.items()]
        a.append(dict(graph=g,mode=m,path=path,q=q,metric=col,median_paired_ratio=statistics.median(values),min_ratio=min(values),max_ratio=max(values),pairs=len(values)))
save('CPU_PLAN_A_INTERFERENCE.csv',a)
audit=dict(status='LIMITATION_CONFIRMED',consumer_controls=controls,corrected_comparison_rows=len(out),new_benchmark_processes=0,original_P2_is_LJ_resident_winner=True,DO_RIE_over_OLD_P2=lj['median_paired_ratio'],service_original_P0_P2_not_measured=True,reason='Initial service gate enumerated only new modes and omitted the original P2. No remeasurement after the fixed 3-process/7-round budget. Universal strongest end-to-end winner remains UNKNOWN.')
(P/'audit/STRONG_BASELINE_LIMITATION.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
notice=f"""
## 최종 강한 대조군 감사 — 반드시 함께 읽을 한계

원본 OLD_P2도 합법적인 비-RCC 기준선이다. 새 RIE가 항상 가장 강하다고 볼 수 없다.
LJ original의 상주 소비자에서 OLD_P2 / PUSH_N은 0.7263배였고,
DO_RIE / OLD_P2의 짝 중앙값은 **{lj['median_paired_ratio']:.4f}배**였다.
같은 adapter의 DO_N에 비해 RIE가 일을 줄여도, frozen P2보다 최종 시간이 짧다는 뜻은 아니다.
정확 discovered count/종료 검사, bridge의 validation/control 구조와 코드 생성 비용이 다르며,
그 각각의 시간 기여를 분리 측정하지 않았으므로 특정 한 연산을 원인으로 단정하지 않는다.

초기 서비스 후보 목록에서 OLD_P0/OLD_P2를 누락했다. `config/service_modes.txt`와 초기 집계는
그대로 보존했고, 추가 CPU benchmark는 실행하지 않았다. CPU_INCREMENTAL_VALUE.csv는 기존 raw만
재집계하여 OLD_P0/OLD_P2까지 포함한 최강 resident 대조군으로 수정했다.
초기 파일은 results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv에 보존했다.

따라서 Push+RCC_TABLE의 cold q32 0.7999배(PUSH_N 대비),
0.8999배(이번에 서비스에서 측정한 순차 DO_RIE 대비)는 실제 측정 범위의 성과다.
**동일 owned-output 계약의 원본 P2 전체 서비스까지 포함한 최종 승자는 UNKNOWN**이다.
과거 P2의 0.840713 수치를 이번 결과에 섞어 그 빈칸을 메우지 않는다.
최소 추가 증거는 frozen P2의 순차/ready 서비스와 Push+RCC_TABLE을 동일 출력 계약으로 짝 비교하는 것이다.
이번 3개 CPU 프로세스 × 7회 한도를 초과해서 그 보완 실험을 숨겨 실행하지 않았다.

GPU pilot은 두 후보의 정확성만 확인했으므로 이 CPU 대조군 누락을 보완하지 않는다.
GPU graph-version mismatch/할당 실패/dispatch cap을 실제 오류로 주입하지 않았고,
그 부분은 CPU 검사 또는 정적 guard에 머문다. 실제 GPU의 cancellation/source 교대와 전체 배열 검사는 PASS다.
"""
for name in ('README_FIRST_KO.md','FINAL_DECISION.md','COST_AND_INTERFERENCE_ANALYSIS.md','SOURCE_BASELINE_RECONCILIATION.md'):
    p=P/name;text=p.read_text(encoding='utf-8')
    if '## 최종 강한 대조군 감사' not in text:
        first,rest=text.split('\n',1);p.write_text(first+'\n'+notice+'\n'+rest,encoding='utf-8')
p=P/'REPRODUCE.md';text=p.read_text(encoding='utf-8')
if '최종 집계 감사는' not in text:text+='\n최종 집계 감사는 `python tools/report.py` 다음 `python tools/strong_control_audit.py` 순서다. 후자는 기존 CSV만 읽으며 성능 실행을 하지 않는다.\n'
p.write_text(text,encoding='utf-8')
# q-by-q A interference is explicitly separated from service completion.
picked=[r for r in a if r['graph']=='livejournal_sampled_4096' and r['q']=='32' and r['mode'] in ('PUSH_RCC_TABLE','DO_RIE') and r['path'] in ('csr','deferred','concurrent')]
text='\n## A 간섭 짝 비교 (LJ original q32)\n\n| Mode | Path | Metric | Median ratio / PUSH_N service |\n|---|---|---|---|\n'
for r in picked:text+=f"| {r['mode']} | {r['path']} | {r['metric']} | {r['median_paired_ratio']:.4f} |\n"
text+='\n미세한 차이나 간섭 1% 이하를 판정하지 않는다. A completion에는 선행 할당·thread 시작·인증 공개가 포함된다.\n'
p=P/'COST_AND_INTERFERENCE_ANALYSIS.md';previous=p.read_text(encoding='utf-8').split('\n## A 간섭 짝 비교')[0];p.write_text(previous+text,encoding='utf-8')
summary=json.loads((P/'results/FINAL_SUMMARY.json').read_text(encoding='utf-8'));summary['strong_service_baseline_limit']=audit
(P/'results/FINAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
# Record the paid historical work in the warmed-certificate condition.
hist=collections.defaultdict(list)
for session in range(3):
    for r in rows(f'results/gate_{session}.csv'):
        if r['certificate']=='warm':hist[(r['graph'],r['schedule'],r['mode'])].append(r)
cost=[]
for (g,s,m),v in hist.items():
    cost.append(dict(graph=g,schedule=s,mode=m,prior_requests=3,measured_current_requests=33,median_current_ns=statistics.median(float(r['ns']) for r in v),median_priming_ns=statistics.median(float(r['priming_ns']) for r in v),median_history_plus_current_ns=statistics.median(float(r['ns'])+float(r['priming_ns']) for r in v),classification='CALCULATED_SUM_OF_MEASURED_RESIDENT_COMPONENTS; reverse preparation excluded'))
save('CPU_CERTIFICATE_HISTORY_COST.csv',cost)
print(json.dumps(audit,ensure_ascii=False))
