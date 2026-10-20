# 비용과 간섭 — 새 CPU 실측

## 최종 강한 대조군 감사 — 반드시 함께 읽을 한계

원본 OLD_P2도 합법적인 비-RCC 기준선이다. 새 RIE가 항상 가장 강하다고 볼 수 없다.
LJ original의 상주 소비자에서 OLD_P2 / PUSH_N은 0.7263배였고,
DO_RIE / OLD_P2의 짝 중앙값은 **1.0505배**였다.
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


3개 독립 worker 프로세스가 순서대로 활성화돼 각각 7회 측정했다.
동시에 3개 benchmark를 실행하지 않았다. 총 25.66초이며 실패/성능 재시도·임계값 튜닝·warmup은 0회다.
진단 계수 코드와 비계측 timing template을 분리했다. 프로세스 RSS 최고값은 [22844, 22880, 23024]KiB다.
이는 preload된 모든 fixture/정답/역인덱스까지 포함한 프로세스 고수위이며 개별 서비스 payload와 같지 않다.

## Resident consumer, LiveJournal original 33요청

아래 기준은 PUSH_N이다. q32는 첫 요청 1개+후속 32개다. 역인덱스는 resident 상태다.
certificate cold는 Executor 초기화/증거 생성부터, warm은 과거 요청 3개를 수행한 상태부터 잰다.
warm의 priming_ns를 숨기지 않고 원시에 보존한다. graph/reverse/workspace 구성은 resident 측정 경계 밖이다.
모든 새 결과 복사·증거 갱신·cache 생성 및 Executor 파괴는 resident 구간에 포함된다.
검증과 반환된 결과의 해제는 별도 validation_ns/release_ns다.

| mode | ratio | wins | edges_saved |
|---|---|---|---|
| OLD_P0 | 1.0148 | 5/21 | -87282 |
| OLD_P2 | 0.7263 | 21/21 | 642244 |
| DO_N | 0.7922 | 20/21 | 642244 |
| DO_RIE | 0.7588 | 21/21 | 643391 |
| PUSH_RCC_TABLE | 0.7946 | 20/21 | 298187 |
| DO_RIE_RCC_TABLE | 0.7566 | 21/21 | 643391 |

DO_RIE_RCC_TABLE / DO_RIE의 짝 중앙값은 1.001252.
추가 edge/vertex-test 생략은 0/0이다. 1에 가까운 타이밍 흔들림을 추가 알고리즘 효과로 인정하지 않는다.

## 실제 서비스 q32

A는 frozen plan_a 그대로 실행한다. A 이후 결과 복사·증거를 만들기 위한 count/scan도 A completion에 포함한다.
A-compute와 completion은 원시 CSV의 별도 필드다.
builder의 COUNT/scan/cursor/scatter/verify와 동기화/join, 실제 workspace 할당을 총시간에 포함한다.
ready의 역사적 reverse 구축 시간은 service window 밖에 별도 기록하고 history-inclusive 합도 표시한다.
이를 cold wall-clock 실측으로 이름 붙이지 않는다.
입력 파일 parsing/CPU 정답검증은 컴퓨팅 구간 밖이며 GPU 결과에 CPU 구축시간을 GPU 변환시간으로 바꾸지 않는다.

| mode | path | ratio | history_inclusive | wins |
|---|---|---|---|---|
| PUSH_N | csr | 1.0000 | 1.0000 | 0/21 |
| PUSH_WCC | csr | 1.0493 | 1.0493 | 2/21 |
| LAST_RESULT_REUSE | csr | 0.9977 | 0.9977 | 12/21 |
| DO_N | deferred | 0.9092 | 0.9092 | 21/21 |
| DO_N | concurrent | 0.9491 | 0.9491 | 17/21 |
| DO_N | ready | 0.7877 | 0.9133 | 21/21 |
| DO_RIE | deferred | 0.8941 | 0.8941 | 18/21 |
| DO_RIE | concurrent | 0.9343 | 0.9343 | 18/21 |
| DO_RIE | ready | 0.7716 | 0.8952 | 20/21 |
| PUSH_RCC_LAST | csr | 0.8151 | 0.8151 | 21/21 |
| PUSH_RCC_TABLE | csr | 0.7999 | 0.7999 | 20/21 |

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

## A 간섭 짝 비교 (LJ original q32)

| Mode | Path | Metric | Median ratio / PUSH_N service |
|---|---|---|---|
| DO_RIE | deferred | a_compute_ns | 1.0473 |
| DO_RIE | deferred | a_completion_ns | 1.0535 |
| DO_RIE | concurrent | a_compute_ns | 1.0492 |
| DO_RIE | concurrent | a_completion_ns | 2.3947 |
| PUSH_RCC_TABLE | csr | a_compute_ns | 1.0086 |
| PUSH_RCC_TABLE | csr | a_completion_ns | 1.0386 |

미세한 차이나 간섭 1% 이하를 판정하지 않는다. A completion에는 선행 할당·thread 시작·인증 공개가 포함된다.
