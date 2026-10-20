# Codex Consumer-first × RCC 통합 검토 — 2026-10-21

## 1. 무엇을 확인했는가

최신 Codex ZIP(4,040,604B)의 CRC와 197개 내부 해시, RCC ZIP(2,125,643B)의 CRC와 99개 내부 해시를 각각 확인했다. 공통 5개 `.edges` 입력은 두 프로젝트에서 바이트 단위로 같았다. 신규 GPU/원격 PC/프로파일러/설치/외부 업로드는 없다.

Codex의 9,600개 소비자 시간 행과 300개 실제 서비스 행에서 수치를 다시 계산했다. 기존 source를 별도 빌드하여 C++ 20,350 assertions·4,360 mode-source 비교를 재통과했다. RCC 원본 소스도 별도 빌드하여 348,672 BFS 비교·74,752 상한 부등식을 재통과했다. 이때 제공된 실행파일을 실행하지 않았다. Codex 성능을 새로 같은 PC에서 재현한 것은 아니다.

## 2. 새로운 Codex 결과는 실제 진전이다

소비자는 기존 queue Push/Pure Pull을 보존하고 fixed Direction P2와 stats-Push P3를 추가했다. LJ4096 q8에서 P2/P0 짝 중앙비율 0.612524, q32는 0.723170이다. q8 간선 검사는 386,329→160,393으로 줄었다. 실제 CPU 서비스 q32는 순차 준비 0.840713, 병행 준비 0.865155(각 15/15 짝 승리); 표시 중앙시간은 CSR 2.066075ms, 순차 1.744309ms, 병행 1.782297ms다. **준비 비용까지 포함한 이득이 이번 조건에서 확인됐지만, 병행이 순차를 능가하지는 않는다.**

q1/q2/q8 cold service는 이득 미확인이다. q8 순차 1.039705, 병행 1.103198. ready warm은 좋지만 과거 준비 비용이 별도로 존재한다. q32에서도 병행 A-compute 짝 변화 +0.105%를 1% 비열등성으로 해석하면 안 된다. A-completion은 준비/스레드 시작 때문에 약 두 배다. 공개 완료가 A보다 앞섰다고 보수적으로 확인한 병행 실행은 0/75다.

판정: Codex의 `CPU_CONSUMER_BENEFIT_CONFIRMED / 조건부 END_TO_END_GAIN_CONFIRMED / CONTINUE_SW`는 제공된 기준선/입력/계측 경계 내에서 타당하다. 기존 `TCSC 성능성공 0`은 기존 버전의 판정으로 보존하되, 최신 consumer-first도 계속 0이라고 말하면 안 된다. 새 GPU 이득, 동시 준비의 우월성, 새 알고리즘/하드웨어 신규성은 여전히 미입증이다.

## 3. RCC와 합치기 전에 달랐던 것

RCC의 Direction reference는 outgoing 기반 remaining 추정과 distance==level 검사를 사용한다. Codex P2는 미방문 정점 indegree의 정확한 합 및 bitmap membership을 사용한다. 두 zip의 Direction 절대시간을 직접 섞거나 배율을 곱할 수 없다.

Codex P0에는 n개 발견 조기 종료가 없고 P2에도 exact early-stop은 없다. RCC는 EARLY_N을 필수 대조군으로 갖췄다. 또한 RCC_TABLE의 원 구현은 누적 queue를 쓰지만 Codex P2는 frontier queue를 덮어쓴다. 이 부분을 그대로 연결하면 방문 집합 또는 비용을 잘못 취급할 수 있다.

따라서 두 알고리즘을 모두 억지로 합치는 대신 **소비 알고리즘과 종료 증거를 분리한 공통 adapter**가 최선의 다음 작업이다.

## 4. 이번 답변에서 별도로 구현한 RIE 종료 조건

`remaining = sum(indegree(v) for v not yet discovered)`는 Codex P2가 방향 선택용으로 이미 유지한다. 이 값이 0이면 발견되지 않은 정점으로 들어가는 간선이 하나도 없다. 시작점은 이미 발견됐으므로 도달 가능한 미발견 정점이 존재할 수 없다. 따라서 해당 level 경계에서 정확한 전체 BFS 거리를 반환할 수 있다. 정점 상한 n보다 작은 도달 영역에서도 작동할 수 있으며 미래 요청을 참조하지 않는다.

이는 graph theory의 직접적인 충분조건이고, **처음 발견된 학술적 알고리즘이라고 주장하지 않는다**. 기존 방향 정책 카운터를 실제 종료 증거로도 소비하도록 만든 작은 구현이다. GPU에서는 정확한 reduction/atomic·level publication 비용을 별도로 평가해야 한다.

새 프로브는 같은 Codex 정책에서 N-stop, RIE, RCC_LAST/TABLE, RIE+RCC와 동일 유지비 OFF를 구현했다. 새 C++ 비교 87,552건, 상한 부등식 550,224건, fixture 7,128요청 PASS; raw edge Python BFS와 내보낸 864개 전체 배열(2,313,312원소)도 일치했다. GPU·sanitizer는 0회다.

## 5. 합치면 자동으로 더 좋아지지는 않았다

기존 source 순서의 LJ 33요청에서:

| 소비 경로 | 간선 검사 | level 수 | 정점 상태 검사 |
|---|---:|---:|---:|
| Codex 동일 Direction, 종료 추가 없음 | 815,788 | 205 | 479,232 |
| Direction+n 종료 | 815,788 | 203 | 471,040 |
| Direction+RIE | 814,641 | 173 | 368,640 |
| Direction+RCC_TABLE | 814,641 | 174 | 372,736 |
| Direction+RIE+RCC_TABLE | 814,641 | 173 | 368,640 |

**LJ의 두 source 순서 및 vertex-relabel 입력에서는 RIE 이후 RCC를 더해도 추가 간선/level 생략이 0이었다.** TABLE은 그 상태에서도 추가 메모리/갱신 비용을 낸다. 이미 알고 있는 메타데이터로 충분한 조건에 과거 결과 캐시를 억지로 붙일 필요는 없다.

단절 SCC 합성 입력에서는 RIE가 전역 미방문 간선 때문에 0이 되지 않으므로 RCC가 별도 정보를 제공한다. 예를 들어 scc4_d32 원래 순서에서 Direction+RIE 6,542,466→RIE+RCC 3,396,738간선이다. 하지만 이 조건에서도 Push+RCC는 284,064간선으로 더 작았다. **Direction을 느리게 사용하는 기준선을 크게 이겼다는 것만으로 최강 경로라고 주장하지 않는다.**

실제 CPU resident batch 10,584행을 3프로세스×7round로 보존했다. 일부 synthetic의 결합 이득은 크지만 작은 실세계 파생 입력의 결합 추가이득은 미확정이다. CPU는 이 대화의 AMD EPYC 9V74, g++14.2.0/O3이며 Codex i5-14500/g++15.2.0/O2와 다르다. 원본 2.066ms 등과 이번 절대시간을 연결하지 않는다. `original`/`holdout`은 RCC 패키지의 기존 이름이며 새 미열람 test set이 아니다.

## 6. 최선의 다음 연구

1. 검증된 Codex builder·Direction을 유지한다. 병행 builder를 주제로 다시 확장하지 않는다.
2. Push+EARLY_N, Direction+N/RIE를 반드시 포함한 뒤 RCC의 **추가 가치**를 같은 backend에서 측정한다.
3. reverse를 요구하지 않는 Push+RCC와, reverse가 필요한 Direction 계열은 warm 소비와 실제 cold 전체비용을 분리한다. 결과 캐시의 생성/갱신, WCC 준비, 같은 source 재요청의 결과 재사용도 공정하게 다룬다.
4. RCC가 이기지 못하는 조건은 결합하지 않는다. 큰 합성 배율만 따라가지 않는다.
5. 기존의 완전 거리 출력 계약과 버전/수명 안전성을 지키는 CPU adapter를 완성한 뒤, 실행 가능한 CUDA harness의 정적 준비와 작은 GPU 승인안을 만든다. 현재 승인에는 GPU 실행이 없다.

## 7. 작업 분담

- Codex: 집 CPU에서 same-backend 통합, 소비자·증거의 factorial 비교, cold/warm service 연결, GPU harness 정적 준비.
- ChatGPT 독립 트랙: 종료 증거의 수학적 충분조건/반례와 최소 상태 표현. 이번에는 RIE와 bridge를 실제로 구현·검증해 제공했다. 다음 결합 후보는 과거 closure가 종료뿐 아니라 검사 대상 영역도 줄일 수 있는지다. 이는 **후속 가설**이며 현재 구현·성능으로 계산하지 않는다.
- 서로의 원본/진행 중 작업을 바꾸거나 GPU 자원을 공유 실행하지 않는다. 미래 자동 연구나 백그라운드 작업이 예약된 것은 아니다.

## 근거 위치

Codex 원본: `FINAL_DECISION.md`, `CONSUMER_VALUE_REPORT_KO.md`, `COST_AND_INTERFERENCE_ANALYSIS.md`, `src/consumers.cpp`, `src/bench.cpp`, `frozen/independent_builder.hpp`, `results/CONSUMER_RAW_TIMINGS_LONG.csv`, `results/PREPARATION_PLUS_CONSUMER_RESULTS.csv`.
RCC 원본: `include/rcc.hpp`, `include/baselines.hpp`, `docs/DESIGN_AND_PROOF_KO.md`, `RESULTS_KO.md`.
새 독립 결과: `independent_bridge/results/BRIDGE_WORK_SUMMARY.csv`, `BRIDGE_PAIRED_SUMMARY.csv`, `test.json`, `PYTHON_ARRAY_CHECK.json`.

기존 Direction-optimizing 원리의 primary reference: Beamer et al., Direction-Optimizing Breadth-First Search (SC2012), https://www.scottbeamer.net/pubs/beamer-sc2012.pdf . GAP Benchmark Suite는 별도의 고성능 reference이며 이번 프로브에서 빌드·실행하지 않았다: https://github.com/sbeamer/gapbs . 이 제한된 문헌 대조만으로 RCC/RIE의 전세계 최초성/부재를 증명하지 않는다.
