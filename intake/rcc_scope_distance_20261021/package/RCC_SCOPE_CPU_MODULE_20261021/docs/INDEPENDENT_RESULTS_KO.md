# 독립 연구 결과: RCC를 종료에서 검사 제외로 확장

2026-10-21. Codex 진행 작업/집 PC/GPU에 접근하지 않은 독립 CPU 라운드다.

## 결론
**RIE+RCC 종료 이후에도 실제로 생략할 수 있는 간선 검사를 찾아 코드로 구현했다. 그러나 현재 실세계 파생 입력에서 안정적인 최강 CPU 시간 우위는 확보하지 못했다.**

공간 범위를 제한하는 `closure_scope.hpp`와 과거 거리로 이번 level의 불가능한 후보를 거르는 `distance_guard.hpp`를 만들었다. 두 모듈 모두 정확한 전체 거리 배열을 반환한다. 이름을 붙인 프로토타입이지 학술적 최초성이나 GPU 성능의 인증이 아니다.

## 1. 1차 설계: 공간 범위
과거 완료 BFS의 R=Reach(r)에 새 source가 속하면 R 밖은 검사하지 않는다. 순수 종료 RCC와 달리 검색 중 매 Pull 레벨의 후보 집합을 줄인다. 같은 캐시 유지비를 내지만 범위는 쓰지 않는 COUNT_ONLY, 전역 정책 유지형, 범위 안 정책형, 미방문 목록 compact형을 모두 비교했다.

12개 입력×2개 source 순서, q8/q32를 고정했다. 9개 입력은 이전 bridge에서 가져왔고 3개는 원리를 확인하려 만든 합성 반례/양성 witness다. `legacy`는 이미 본 순서이고 `unique`는 이번 timing 전에 고정한 33개 서로 다른 source 순서다. 새 실제 graph holdout은 아니다. 즉시 반복된 동일 source는 모든 구현에서 기존 결과를 재사용한다.

합성 scc4의 legacy q32에서 COUNT_ONLY→SCOPE_GLOBAL은 간선 검사 3,296,735→249,311, 짝 중앙 속도비 4.774배였다. 그러나 같은 비교군의 Push+RCC_TABLE보다 여전히 느렸다. one-way connected 합성 입력에서도 공간 범위 축소는 동작하지만, 이것만으로 더 강한 Push를 이기지는 못했다.

LiveJournal legacy에서는 범위가 거의 전체 graph라 간선 검사 추가 감소가 0이었다. Google의 같은 순서도 공간 제한으로 간선 검사가 줄지 않았다. 작은 시간 변동을 새 작업 생략 효과로 인정하지 않는다.

별도로 기존 미방문 목록 compaction과 WCC scope를 구현해 비교했다. 단절 graph에서 WCC가 같은 범위 정보를 줄 수 있으므로, 공간 축소의 큰 배율을 독립 신규성으로 주장하지 않는다. WCC 구축비도 각 배치에 포함했다. 이 구현들은 정확성을 확인한 CPU 참조이며 GAP/cuGraph 최신 최고성능 라이브러리의 재현은 아니다.

## 2. 2차 설계: 도달 ‘거리’를 보유하면 연결된 입력에서도 제한 가능
R의 원소만으로 부족하므로, 이미 완성된 직전 BFS의 거리 배열 하나를 보유한다. 추가 간선 스캔이나 reverse 구축을 하지 않고 완료 후 buffer swap을 사용한다. 추가 retained array는 4n바이트이며 전체 결과 반환은 별도의 복사로 타이밍에 포함했다.

- LAST_COUNT: 기존 cardinality 종료만 사용.
- LAST_CLOSURE: 범위 밖 목적지 제외.
- LAST_RADIUS: d_old(v)>d_old(s)+level+1인 이번 후보 제외.
- LAST_FRONTIER: d_old(v)>1+max(d_old(frontier))인 이번 후보 제외.

모두 같은 Direction+정확한 RIE+cardinality 종료 코드 경로를 사용한다. 후보를 나중으로 미루는 것이지 최단거리를 근사하거나 정답을 이전 거리로 덮어쓰는 것이 아니다.

### 실제 파생 입력의 추가 작업 생략
첫 요청+후속32회, 동일 source 순서. 즉시 같은 source 재사용을 모든 방식에 적용했으므로 이전 bridge의 수치와 직접 감산하지 않는다.

| 입력/순서 | Direction+RIE 간선 검사 | LAST_FRONTIER | 감소 |
|---|---:|---:|---:|
| Google legacy | 265,846 | 203,808 | 23.336% |
| Google unique | 157,045 | 148,361 | 5.530% |
| LiveJournal legacy | 810,522 | 762,249 | 5.956% |
| LiveJournal unique | 806,503 | 796,918 | 1.188% |

두 LiveJournal 순서에서 cardinality RCC만의 추가 간선 생략은 0이었다. 따라서 과거 ‘거리 값’은 RCC 크기와 RIE 카운터만으로는 제공하지 못한 실제 작업 제외 근거를 주었다. 이는 계산상 실제 간선 probe 감소이며 GPU 명령/DRAM 바이트/시간 가속률과 같지 않다.

## 3. CPU에서 왜 바로 빨라지지 않았는가
추가 증거를 읽고 판정하는 비용도 있다. legacy q32의 논리적 read ledger:

| 입력 | 줄인 neighbor ID 읽기 | 추가 old-distance 읽기 |
|---|---:|---:|
| Google | 62,038회 | 46,496회 |
| LiveJournal | 48,273회 | 270,301회 |
| oneway_dense (합성) | 10,039,546회 | 86,799회 |

각 원소가 4B이므로 LiveJournal의 old-distance 논리 읽기는 약1.081MB, 생략한 neighbor ID는 약0.193MB다. 이것은 명령 수준의 payload 회계이며 캐시 재사용이 있어 DRAM bytes로 해석하면 안 된다. 기존 full n 거리 초기화, 결과 복사, frontier bitmap 등도 남는다.

3프로세스×7round의 resident-reverse/cold-cache 배치를 비교했다. LiveJournal LAST_FRONTIER는 DO_RIE 대비 짝 중앙 속도비 legacy 0.855, unique 0.886으로 각 3프로세스 중앙값 모두 열세였다. Google unique에서 DO_RIE 대비 작은 개선 방향이 있었지만 강한 Push가 훨씬 빨랐고, 유의한 범용 이득으로 판정하지 않았다.

**간선을 덜 읽는다는 증거는 얻었지만, 그 증거를 활용하는 추가 비용이 이득을 먹을 수 있다.**

## 4. 제한적인 양성 사례
직접 만든 `oneway_dense`는 하나의 WCC 안에 방향성으로 연결된 밀집 영역이 있는 합성 witness다. legacy q32의 LAST_FRONTIER는 Push+RCC_TABLE 대비 짝 중앙 1.639배, 21쌍 중19승, 3프로세스 중앙 모두 개선 방향이었다. DO_RIE와 비교하면 13.585배지만 그것은 이 입력에서 훨씬 불리한 소비 경로라 주 성과로 사용하지 않는다.

새 무중복 source 순서에서는 같은 LAST_FRONTIER가 Push+RCC_TABLE보다 느렸다(짝 중앙속도비0.346). 따라서 요청 지역성이 있는 조건부 효과일 뿐이며, 합성 graph/특정 source 분포에 의존한다. FullBitset, GAP, cuGraph, GPU 및 모든 알려진 indexing 기법 대비 우위는 검증하지 않았다. reverse를 이미 준비한 resident 경계이고 2차 guard의 cold reverse 포함 결과는 없다.

## 5. 실제 수행한 검증

| 검사 | 1차 Scope | 2차 DistanceGuard |
|---|---:|---:|
| C++ mode-query 정답 비교 | 416,768 | 51,200 |
| 테스트 graph 구성 | 4,736 | 640 |
| 보존 fixture 요청 정답 | 8,712 | 6,336 |
| 독립 Python 전체 거리 배열 | 1,056 | 768 |
| 비계측 timing CSV | 13,464행 | 4,032행 |

두 테스트군에는 겹치는 tiny graph와 기존 baseline이 포함된다. 467,968개 독립 실제 graph를 검사했다는 뜻이 아니다. Python 독립 배열 총1,824개/4,440,984원소는 raw .edges와 deque BFS에서 재계산했다. 2차 Python은 n=3 directed graph512개에서7,824개 삼각부등식과12,360개 frontier 간선 bound를 추가 확인했다.

GPU/원격 PC/Nsight/sanitizer/외부 업로드/설치 모두0회. 단일 소유자 CPU 참조의 범위다.

## 6. 타이밍/자원 한계
이번 머신은 Intel Xeon Platinum 8573C, g++14.2.0/O3. 이전 ChatGPT EPYC 또는 Codex i5 수치와 절대시간/가속률을 곱하지 않는다. 공유 컨테이너의 타이밍 분산이 크고 모든 이상값을 보존했다. 3프로세스는 독립 서버/날짜 반복이 아니다.

1차는 reverse resident 및 별도의 cold reverse 구축을 검사했고, 2차는 reverse resident만 검사했다. CPU로부터 실제 GPU의 간섭/원인/전력을 추론하지 않는다. 코드별 workspace/retained output/캐시를 포함해 payload를 보고하되 RSS나 전체 allocator peak가 아니다. Push의 raw `levels=0`은 level 계수를 수집하지 않았다는 뜻이다.

## 7. Codex와 합칠 때
진행 중 Codex 작업을 변경하거나 메시지를 보내지 않았다. 본 모듈은 다음 결과가 도착하면 감사·통합할 후보일 뿐, 현재 Codex 프롬프트를 덮어쓰지 않는다.

1. Codex가 유지하는 Direction+RIE와 같은 backend에서 guard의 work-count를 먼저 대조한다.
2. 추가 CPU 비용 때문에 실제 입력에서는 guard를 기본 활성화하지 않는다.
3. RIE와 cardinality로 이미 설명되는 종료 효과, scope 후보 제외, 시간적 distance 제외를 별도 ON/OFF로 평가한다.
4. GPU 적용 전에는 정확한 이전 거리 배열·frontier max reduction·publication/결과 수명 비용을 검토한다. 이번 결과는 새 GPU 실행 승인서가 아니다.
5. 새로운 H/W가 필요하다는 결론은 없다. 현재 자료는 “추가 판정 비용보다 생략 가능한 실제 메모리 요청이 충분한가?”라는 구체적인 질문과 모듈을 제공한다.

## 현재 판정
`EXACT_CANDIDATE_PRUNING_IMPLEMENTED / REAL_DERIVED_WORK_REDUCTION / CPU_BENEFIT_CONDITIONAL_SYNTHETIC_ONLY / GPU_UNMEASURED / NOVELTY_NOT_ESTABLISHED`.
