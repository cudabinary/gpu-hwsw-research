# 제한된 선행기술 대조

이 라운드는 새로운 모듈 구현과 반증에 집중했다. 아래 primary source 대조는 관련 원리의 존재를 확인한 것이며 모든 선행기술 조사나 전세계 최초성 인증이 아니다.

1. Beamer, Asanović, Patterson, Direction-Optimizing Breadth-First Search, SC2012.
   https://www.scottbeamer.net/pubs/beamer-sc2012.pdf
   작은/큰 frontier에 따른 Push/Pull 전환은 기존 기술이다. 본 코드는 전달된 Codex alpha=15/beta=24 정책을 비교 기반으로 사용한다.
2. GAP Benchmark Suite, BFS implementation.
   https://github.com/sbeamer/gapbs/blob/master/src/bfs.cc
   공개 고성능 참조 구현은 존재하지만 본 세션에서 다운로드·빌드·실행한 것은 아니다. 본 CPU 코드가 GAP를 능가했다고 주장하지 않는다.
3. Goldberg, Harrelson, Computing the Shortest Path: A* Search Meets Graph Theory, MSR-TR-2004-24 / SODA2005.
   https://www.microsoft.com/en-us/research/publication/computing-the-shortest-path-a-search-meets-graph-theory/
   landmark와 삼각부등식으로 최단거리 하한을 이용하는 원리는 선행한다. 본 DISTANCE_RADIUS/FRONTIER_MAX의 수학 원리 자체를 신규라고 할 수 없다. 이 원문은 point-to-point 질의이고 본 실험은 전체 단일 source 거리 배열/이전 온라인 결과 재사용이라는 계약 차이가 있지만, 그것만으로 독립 신규성이 확정되지 않는다.
4. Akiba, Iwata, Yoshida, Fast Exact Shortest-Path Distance Queries on Large Networks by Pruned Landmark Labeling, SIGMOD2013.
   https://arxiv.org/abs/1304.4661
   이전 BFS에서 만든 레이블로 이후 BFS를 가지치기하는 관련 연구다. 본 모듈은 레이블 구축/질의 시스템을 구현한 것이 아니며 PLL과 직접 성능 비교하지 않았다.
5. Besta et al., SlimSell (IPDPS2017, arXiv extended version).
   https://arxiv.org/abs/2010.09913
   BFS의 작업량과 레이아웃을 함께 줄이는 선행 사례다. 성능은 작업량뿐 아니라 표현/벡터화 비용에도 달려 있다는 비교 배경으로만 사용했다.

신규성 후보는 고전 원리의 이름 변경이 아니다. 현재는 한 개의 완료된 runtime 결과를 사용해 실제 수행할 불규칙 메모리 요청을 적은 비용으로 줄일 수 있는 구체적 구현 가능성을 시험했다. 실세계 파생 CPU 입력에서 시간 우위를 확보하지 못했으므로 고수준 범용 시스템/하드웨어 신규성을 주장하지 않는다.
