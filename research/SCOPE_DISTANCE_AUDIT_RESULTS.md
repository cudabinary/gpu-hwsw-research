# RCC-Scope / DistanceGuard 독립 감사 — 2026-10-21

**무결성·구현·검사한 CPU 정확성 PASS. 실제 추가 간선 생략 재현. 실세계 파생 입력의 강한 전체 서비스 우위와 신규성은 미확립. 기본 RCC 통합 보류.**

## 원본·증거 출처

입력 `RCC_SCOPE_DISTANCE_CPU_20261021.zip`은 **2,528,431 bytes**, SHA256 **`c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c`**다. 원본 Downloads 파일을 수정하지 않았고 `intake/rcc_scope_distance_20261021/original.zip`에 같은 bytes/SHA로 복사했다. ZIP 93개 파일, CRC PASS, 경로/중복/심볼릭 링크 검사 PASS, MANIFEST의 92개 대상 파일을 누락·추가 없이 크기/SHA로 확인했다. 매니페스트 자신은 93번째 파일이다. 이 검사는 내부 일치와 파일 동일성을 입증하며 외부 서명/저자 실명·신규성을 인증하지 않는다.

별도 `package/` 추출본도 같은 매니페스트를 통과했다. 공통 Builder/consumer header/consumer source/stop_bridge 4개와 기존 공유 fixture 9개가 현재 vendor와 byte-for-byte 동일하다. 첨부된 ELF 바이너리는 실행하지 않았다. 읽은 C++ 소스를 기존 로컬 g++로 새로 컴파일했고, 출력은 이 worktree의 별도 build/results에만 썼다. 패키지 문서의 명령·통합 제안은 실행 권한으로 취급하지 않았다.

입력 문서, 두 header와 probe, fixture 생성/검증·재집계 도구 및 원시 결과를 읽었다. 원본 source/log/오류 기록을 수정하지 않았다. 상세 receipt는 `intake/.../INTAKE.json`, 새 감사 증거는 `results/scope_distance_audit_20261021/`다.

## 독립 정확성 감사

| 검사 | 이 감사에서 확인한 결과 |
|---|---|
| 새 빌드 Scope C++ test | 4,736 graph 구성, 416,768 mode-query 비교 PASS |
| 새 빌드 DistanceGuard C++ test | 640 graph 구성, 51,200 mode-query 비교 PASS |
| 제공 probe의 새 fixture diagnose | Scope 8,712 + Guard 6,336 전체 요청 PASS |
| 새 공통 owned-output diagnose | 12 graph×2 source 순서×16 mode×33 요청 = 12,672 전체 배열 PASS; executor 파괴 뒤 보유 출력도 불변 |
| Python raw-edge deque BFS | 제공 배열 1,824개/4,440,984원소, 새 제공-probe 배열 동일 수, 새 owned harness 1,536개/3,739,776원소 PASS |
| 독립 유한 수학 검사 | n=3 directed graph 512개, closure 7,824 / triangle 7,824 / frontier edge 12,360개 조건 PASS |
| 반례 | 부분 BFS prefix를 closure로 사용, incoming/outgoing 질량 혼동, frontier MIN 사용, 일시 제외를 영구 미도달로 표시하는 4개 잘못된 규칙을 재반증 |

전체 배열 수는 중복 요청과 동일 tiny graph/baseline이 포함된 검사 수다. 각 행을 고유 실제 graph 또는 독립 통계 표본으로 더하지 않는다. 독립 Python oracle key는 12개 입력의 86개 graph-source이며, 재생성과 제공 배열의 일치는 새로운 실세계 표본을 뜻하지 않는다.

원본 Scope와 Guard의 진단 CSV를 새 공통 harness와 대조한 **14,256 mode-query 행**에서 `edges/vertex_tests/levels`가 정확히 일치했다. 원본 과거 timing은 Guard 4,032행/짝요약120개, Scope 13,464행/시간요약792개를 원시 CSV에서 재계산해 일치시켰다. 공유 컨테이너의 과거 시간과 이번 로컬 시간을 합치거나 배율을 곱하지 않았다.

Scope의 immutable closure publication, 예산 거부·주입된 publication 할당 실패·부분 탐색 시 이전 인증 유지·잘못된 graph/reverse identity 거부, Guard의 중단 후 재개가 아닌 새 정확 실행·zero-cache 경로를 소스와 제공 test 재실행으로 확인했다. helper는 trusted 내부 Domain/workspace를 받으며 임의 외부 배열 검증용 API가 아니다. 전체 owned 결과 반환과 cache publication 전 출력 할당은 새 공통 harness에서 별도로 구현했다.

## 동일 전체 서비스 계약

`research/SCOPE_DISTANCE_PROTOCOL.json`을 성능 실행 전에 고정했다. 기존 g++15.2/C++20/O2에서 **3개 순차 worker×7 round×정확한 반대 순서 2 sweep**을 실행했다. warmup/성능 재시도0. Google/LJ/LJ relabel과 합성 scc4/oneway_dense, legacy/unique source, q8/q32, cold/ready, 16개 policy로 **26,880 trials / 564,480 전체 배열**이 모두 맞았다. 전체 wall time은 약49.23초였고 각 worker peak RSS는 20,444 KiB다.

모든 policy는 같은 resident immutable CSR, 같은 frozen reverse Builder, 같은 workspace 계열, 동일 source의 즉시 반복에 대한 통상적인 exact-result reuse를 사용했다. 첫 요청 전 인증은 비어 있다. q는 첫 요청+후속 q개를 뜻한다. 모든 실제 반환은 immutable owned 전체 거리 배열이며, 새 배열은 인증 publication 전에 할당한다. 즉시 같은 source는 이미 owned인 동일 정답을 재사용해도 소유 수명이 유지된다.

주 지표 `service_ns`는 출력 포인터 vector reserve, cold의 reverse 구축, workspace/cache 준비, 모든 요청의 계산·인증 갱신·owned 결과 복사, executor/workspace/reverse teardown을 포함한다. 입력 I/O/CSR 파싱, ready의 과거 reverse 준비, oracle 검증, 마지막 소비자의 출력 해제는 제외한다. 준비·query+publication·과거 reverse 구축·검증·마지막 출력 해제를 따로 기록했다. `lifecycle_ns`는 ready 준비부터 검증·출력 해제까지 연속 측정하며 실험용 검증이 포함된다. 검증 없는 운영 지연이라고 부르지 않는다.

**이번 배치에서는 각 policy가 같은 첫 source를 자기 알고리즘으로 처리한다.** 직전 OLD_P2 고정 외부 A 파이프라인과 측정 경계가 다르므로 그 결과와 비율을 혼합하지 않는다. 새 공통 harness 안의 모든 대조군은 동일 계약이다. 공통 API 어댑터의 추가 CSR/출력 복사와 Trace=true 비용을 측정한 API 성능 실험이라고 확대하지 않는다.

통계 단위는 두 mirror 비율을 기하평균한 session/round 짝 block 21개, session3개다. gate는 중앙 candidate/baseline <0.95, 17/21 이상 승리, 3 session 중앙값 모두 <0.95다. outlier를 제거하거나 결과에 따라 경로/source/threshold를 선택하지 않았다. 이는 다중 비교를 보정한 검정/신뢰구간이 아니며 장기·다른 날짜 재현도 아니다. 640개 같은-policy mirror 대조의 중앙값 범위가 0.772~1.281이고 raw 최댓값은 7.60배였다. 원시 잡음과 모든 극값을 보존했다.

## 고유 작업 생략

아래는 첫 요청+32후속 요청의 동일한 source 순서다. 기존 RCC TABLE을 함께 쓰는 Direction+RIE와도 직접 대조했다.

| 입력/순서 | Direction+RIE+RCC TABLE edges | DIST_FRONTIER edges | 추가 생략 | 추가 old-distance 논리 읽기 |
|---|---:|---:|---:|---:|
| Google legacy | 265,846 | 203,808 | 62,038 (23.34%) | 46,496 |
| Google unique | 156,882 | 148,361 | 8,521 (5.43%) | 19,881 |
| LJ legacy | 810,522 | 762,249 | 48,273 (5.96%) | 270,301 |
| LJ unique | 806,503 | 796,918 | 9,585 (1.19%) | 224,699 |

matched DIST_COUNT→CLOSURE→RADIUS→FRONTIER에서도 분석했으며 같은 이전 배열·갱신 방식의 filter 차분을 보존했다. Google/LJ legacy의 DIST_COUNT와 FRONTIER는 레벨 수·정점 검사 수가 같아 단순한 종료 단축으로만 설명할 수 없다. Google unique의 DO_RIE+TABLE 대비 레벨 수는 같다고 가정하지 않았다. 모든 대조는 `MECHANISM_LEDGER.json`과 `WORK_SUMMARY.json`에 있다.

Scope GLOBAL은 Google/LJ legacy에서 추가 edge 생략0을 재현했다. LJ의 정점 검사만 364,544→364,461로 작게 줄었다. scc4 legacy의 COUNT→GLOBAL은 edge 3,296,735→249,311, vertex 135,168→39,936이지만 이 큰 합성 배율이 강한 Push 대비 시간 우위를 뜻하지 않았다. WCC/compaction 대조군도 같은 서비스 창에서 비용을 지불했다.

## 강한 기준선 대비 시간

아래는 **DIST_FRONTIER / 기준선**의 `service_ns` 짝 중앙 비율, ready q32다. 1보다 작으면 Guard가 빠르다. 시간 중앙값끼리 나눈 값이 아니다.

| 입력/순서 | / RCC TABLE | / RCC LAST | / OLD_P2 | / Direction+RIE | / Direction+RIE+TABLE |
|---|---:|---:|---:|---:|---:|
| Google legacy | 2.2783 | 2.1150 | 1.0411 | 1.0833 | 1.0636 |
| Google unique | 2.1677 | 2.2453 | 1.0814 | 1.1148 | 1.0970 |
| LJ legacy | 0.9733 | 0.9580 | 1.0575 | 1.1276 | 1.1017 |
| LJ unique | 0.9901 | 0.9649 | 1.0900 | 1.1261 | 1.1116 |
| LJ relabel legacy | 1.7862 | 1.7498 | 1.0320 | 1.0977 | 1.1151 |
| LJ relabel unique | 1.6212 | 1.6163 | 1.0889 | 1.1352 | 1.1325 |

Google/LJ의 strong 전체시간 우위를 확보하지 못했다. LJ에서 RCC만과 비교한 작은 개선 방향도 5%/3-session gate를 통과하지 못했고 OLD_P2/RIE보다 느렸다. Scope GLOBAL/LOCAL/COMPACT는 40조건 중 모든 고정 대조군을 통과한 조건이 0이었다.

**유일한 전체 gate 양성은 합성 `oneway_dense / legacy / q32 / ready`의 DIST_FRONTIER**였다. RCC TABLE 대비0.8730 (약12.70% 시간 감소), LAST 대비0.8616이며 두 경우21/21 승리·3session 모두5% 이상 이득이었다. frontier를 쓰지 않는 DIST_RADIUS 대비0.5960으로 matched ablation도 통과했다. PUSH_N, RCC TABLE/LAST, OLD_P2, RIE, RIE+TABLE, compaction, WCC의 사전 고정8개 대조군을 모두 통과했다.

그러나 같은 조건에서 cold reverse 포함 RCC TABLE 대비2.0234, ready+실제 과거 준비 비용 포함2.0278이었다. 같은 graph의 unique ready q32에서는3.9124였다. 따라서 **이미 준비된 reverse + 특정 합성 graph + 지역적인 요청**의 한정 witness다. 이 조건을 사전에 저렴하게 식별하는 온라인 선택 규칙은 구현·검증하지 않았다. 두 확장을 합성한 새 알고리즘도 만들지 않았다.

사전 선언한 matched 비교 외에 FRONTIER 대 Scope GLOBAL/LOCAL/COMPACT 및 DIST_COUNT의 같은 raw 데이터 비교를 추가 보존했다. CSV의 `predeclared_pair=False`로 표시하며 신규 primary 양성/유의성 주장에 쓰지 않았다.

## 준비·유지·메모리 비용

예: LJ legacy cold q32의 실측 시간 중앙값은 다음과 같다. 준비는 reverse가 필요한 경우 실제 Builder 비용을 포함한다. 열별 중앙값의 합이 전체 중앙값과 정확히 같다고 가정하지 않는다.

| Policy | prepare (us) | queries+publication (us) | service (us) | live cache payload |
|---|---:|---:|---:|---:|
| RCC TABLE | 1.389 | 1549.386 | 1551.531 | 16,384 B |
| OLD_P2 | 266.086 | 1400.278 | 1668.887 | 0 B |
| Direction+RIE | 267.964 | 1339.185 | 1612.912 | 0 B |
| Scope GLOBAL | 270.391 | 1524.161 | 1787.933 | 16,892 B |
| DIST_FRONTIER | 265.668 | 1507.337 | 1780.305 | 16,384 B |

Scope는 membership bitmap+정점 목록, 완료 distance[n] scan과 global indegree 합, 교체 시 old+new publication payload를 가진다. COUNT 대조는 이 비용을 함께 지불한다. DistanceGuard는4n retained array와 완료 시 buffer swap을 사용하지만 모든 mode의 owned 반환과 shared exact-result cache 수명 비용은 남는다. LJ legacy의 추가 old-distance 읽기270,301회는4B 기준1,081,204B로, 생략한 이웃 ID48,273회의193,092B보다 많다. 이는 논리적 payload 회계이며 DRAM traffic·cache miss·GPU 명령 측정이 아니다.

`COSTS.json`에 전체 조건의 준비·유지 포함 query·검증·해제·history·lifecycle 비용을 보존했다. 유지 작업만의 독립 micro-timer를 수집하지 않았으므로 임의로 분리된 시간 값을 만들지 않았다. `payload_upper_bytes` 필드는 graph/workspace/live-cache/출력/Builder scratch의 공통 회계지만 Scope의 순간 old+new publication과 allocator metadata를 모두 포함하지 않아 **엄밀한 전역 상한이 아니다**. 이 한계는 `ANALYSIS.json`에도 표시했다. peak RSS와 cache payload를 혼동하거나 이 필드를 hard memory limit 증거로 쓰지 않는다.

## API·원본 보존·통합 판정

API1.0.0, 기본 `src/cpu_module.cpp`, `api/`, `tests/main_client.cpp`, vendor, MAIN worktree를 변경하지 않았다. 기존 `tools/verify.py`를 새로 실행해 **동일 MAIN client SHA `d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e`**에 baseline/TABLE/LAST를 실제 교체했고 각각2,111 배열 PASS였다.

첨부 두 helper 자체에는 `rcc_create/rcc_destroy`, prepare/can_apply/update 계약이 없다. borrowed output과 level-budget 취소도 API의 owned-output/row-budget과 바로 같지 않다. 따라서 **후보의 API 교체 호환성은 NOT_IMPLEMENTED_NOT_VERIFIED**이며 기존 모듈 PASS를 후보의 PASS로 옮기지 않는다. 새 owned harness는 연구용 경계 정합화이며 MAIN에서 로드할 공통 모듈을 배포한 것이 아니다. 기존 공통 계약의 fallback/할당 실패/graph identity·version/출력 수명을 유지할 어댑터 검증 없이 통합하지 않는다.

기본 통합을 보류하고 원본 두 모듈, 정확성·반례·기전·조건부 합성 양성·실제 입력 부정 결과를 독립 후보로 보존한다. 신규성/독립 논문 기여는 `SCOPE_DISTANCE_NOVELTY_AUDIT.md`의 1차 출처 감사 결과 미확립이다. 새 GPU·유료 자원·sanitizer·원본 바이너리 실행은0회다.

vendor37개, 원본 연구 폴더의 대응37개, MAIN tracked219개 파일과 HEAD/status를 전후 대조했다. 기존 OLD_P2 commit `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c`의60개 artifact를 commit blob SHA로 재검증했고, 이전 실험 source/results도 현재 파일과 일치했다. 변화하는 RCC status 문서는 이 새 체크포인트에서 갱신하지만 이전 commit은 그대로 보존한다. 기존 미추적 run과 MAIN의 기존 미추적 파일도 건드리지 않았다.

준비 마지막 단계에서 Linux git가 Windows 형식 worktree 포인터를 읽지 못한 metadata 오류1건이 있었다. 이미 통과한 정확성/API 검사를 재실행하지 않고 기존 main/.git object database를 읽도록 경로만 고쳐 성능 실행 전에 최종 pin을 확정했다. `PREPARE_METADATA_REPAIR.json`에 기록했으며 성능 재시도는0이다.

## 재현과 증거

원본 ZIP을 보존한 새 깨끗한 복사본에서, 기존 WSL Python/g++만 사용한다. 제공된 tools 명령을 자동 실행하지 않는다.

```text
python3 tools/intake_scope_distance.py
python3 tools/audit_scope_distance.py prepare
python3 tools/audit_scope_distance.py benchmark
python3 tools/analyze_scope_distance.py
```

intake/build/results가 이미 있으면 자동 덮어쓰기·성능 재시도를 거부한다. 이 전달 상태에서는 원시 CSV/배열/명령/stdout/stderr/pin/보존 snapshot/통계/기전 ledger를 그대로 읽을 수 있다. 결과의 무결성 영수증은 `results/scope_distance_audit_20261021/ARTIFACT_SHA256.json`, 원격 반영은 로컬 ignored `DELIVERY_STATUS.json`과 `git ls-remote`로 확인한다. MAIN 자동 병합·paper 브랜치 생성은 하지 않는다.
