# RCC-Scope / DistanceGuard 신규성 독립 감사 — 2026-10-21

판정: **NOVELTY_NOT_ESTABLISHED / 독립 논문 기여 미확립 / 기본 RCC 통합 보류**. 실제 구현·정확한 추가 probe 생략·한정 합성 witness는 확인했다. 이 사실과 학술적 최초성, 응용 전체시간 우위, GPU/HW 필요성은 별도로 판정한다.

## 구현한 조건과 증명의 범위

RCC-Scope는 정확히 완료된 BFS의 `R=Reach(r)`가 outgoing-closed임을 이용한다. `s in R`이면 `Reach(s) subset R`이므로 Pull 목적지 후보를 R로 제한할 수 있다. 지역 RIE의 초기 질량은 R에 속한 정점들의 **전역 indegree 합**이다. outgoing[R]와 혼동하지 않은 구현과 반례를 확인했다. COUNT_ONLY/SCOPE_GLOBAL은 같은 certificate 저장·갱신을 사용하여 공간 pruning을 대조한다. LOCAL은 정책 입력과 지역 종료도 바꾸므로 GLOBAL과 같은 기여라고 묶지 않는다.

DistanceGuard의 radius 조건은 `d_old(v) <= d_old(s)+level+1`이고, frontier 조건은 `d_old(v) <= 1+max(d_old(u), u in current_frontier)`다. 각 실제 간선에서 `d_old(v)<=d_old(u)+1`이 성립하므로 이를 위반한 목적지는 이번 Pull 레벨에서 연결될 수 없다. 나중 레벨에서 다시 후보가 되어야 한다. frontier MIN 사용이나 임시 radius 원소 수를 전체 도달 수 상한으로 사용하는 규칙은 틀리다. 이 직접 증명과 코드·유한 전수검사를 대조했다.

Google/LJ의 matched DIST_COUNT와 FRONTIER는 같은 레벨·정점 검사 수를 유지하면서 reverse 간선 probe를 줄였다. 따라서 단순한 RCC count/RIE 종료 효과와 구별되는 실제 후보 제외는 있다. 이 witness는 알고리즘 최초성의 증명이 아니다.

## 직접 확인한 1차 출처

| 선행기술 | 실제 확인한 내용 | 현재 패키지와의 관계·감사 한계 |
|---|---|---|
| [Goldberg–Harrelson ALT, SODA2005, §4](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/01/soda05.pdf) | landmark 거리와 삼각부등식으로 정확한 최단거리 하한을 구성 | radius 조건은 기존 거리 하한을 이번 BFS 레벨에 적용한 것으로 해석된다. frontier MAX도 기존 edge-distance 부등식의 직접 귀결이다. 원문의 point-to-point/A*와 온라인 이전 결과를 쓰는 전체 SSSP/Pull 필터의 계약은 다르다. 같은 프로그램/정확한 동일 선행 구현을 발견했다고 주장하지 않는다. |
| [Akiba–Iwata–Yoshida PLL, SIGMOD2013, §4.2/§6](https://arxiv.org/html/1304.4661v1) | 이전 BFS로 만든 label에 따라 후속 BFS의 정점 확장·간선 탐색을 prune하며 directed 변형도 기술 | “이전 BFS 정보를 써 후속 BFS를 prune한다”는 넓은 신규성 주장은 선행한다. PLL은 2-hop distance index 구축/질의이며 이 패키지는 한 개의 runtime 이전 배열과 임시 목적지 필터다. 계약 차이만으로 신규성이 확정되지는 않는다. |
| [Beamer 등 Direction-Optimizing BFS, SC2012](https://people.eecs.berkeley.edu/~krste/papers/beamer-sc2012.pdf) | top-down/bottom-up 전환과 Pull에서 첫 부모 발견 후 남은 이웃 검사 생략 | 기본 Direction과 edge probe 감소 자체는 기존 기술이다. 현재 frozen P2/RIE는 이 계열의 내부 대조군이며 저자 구현 전체를 재현한 것이 아니다. |
| [GAP BFS 저자 코드](https://github.com/sbeamer/gapbs/blob/master/src/bfs.cc), [raw source](https://raw.githubusercontent.com/sbeamer/gapbs/master/src/bfs.cc) | parent 배열, sliding queue/bitmap, 병렬 Push/Pull 및 alpha=15/beta=18 기본값 | 현재 alpha=15/beta=24 내부 CPU 구현과 성능을 동일시할 수 없다. 본 감사는 소스 확인이며 GAP 빌드/성능 실험은 하지 않았다. 전체 거리 배열·준비·출력 계약을 맞춘 공개 강한 baseline 비교가 여전히 필요하다. |
| [O'Reach, SEA2021](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2021.13) | 정적 그래프 Boolean 도달성 인덱스와 구축/질의/메모리 대조 | RCC-Scope의 도달성 정보 사용은 reachability indexing/집합 재사용과 구별해 평가해야 한다. Boolean 질의 시간을 전체 owned 거리 배열의 분모로 쓰지 않았다. |
| [SlimSell 저자 arXiv 원문](https://arxiv.org/abs/2010.09913) | BFS 표현과 vectorization·작업량을 함께 다루는 관련 연구 | 입력 패키지의 링크가 실제 해당 논문임을 확인했다. 이번 두 필터와 동일한 알고리즘이라고 판정하거나 성능 수치를 직접 비교하지 않았다. |

## 독립 기여에 대한 판단

구현상 차별점 후보는 하나의 완전한 온라인 결과, 4n-byte 거리 보유, 기존 frontier bitmap 생성 루프의 MAX, 정확한 temporary candidate exclusion, 전처리 index 없이 갱신하는 비용 계약이다. 이는 현재 코드의 설계 설명이며 선행연구에 없다는 확정이 아니다.

실제 파생 입력에서 안정적인 강한 전체 서비스 우위를 확보하지 못했다. 한정 양성은 이미 의도적으로 만든 합성 graph/지역 source 요청/ready reverse 조합이고, cold/unique 조건에서 무너졌다. 공개 최고성능 baseline, 새로운 실제 graph/workload holdout, 비용이 이득보다 작아지는 검증 가능한 적용 규칙과 그 선택 비용도 없다. 40조건×여러 후보에 대한 이번 gate는 다중 비교를 보정한 통계 검정이 아니므로 유일한 양성을 논문 성립 근거로 올리지 않는다.

따라서 현재는 정확한 독립 실험 후보·반례·기전 증거로 보존한다. 기본 활성화, 보편 SW 우위, GPU/HW 기여, 독립 논문 후보 승격을 권고하지 않는다. 이 판정은 모든 관련 문헌을 소진하여 “동일 선행 논문이 확정됐다”는 뜻도 아니다.
