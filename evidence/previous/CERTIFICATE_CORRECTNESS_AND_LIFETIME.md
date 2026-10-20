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
