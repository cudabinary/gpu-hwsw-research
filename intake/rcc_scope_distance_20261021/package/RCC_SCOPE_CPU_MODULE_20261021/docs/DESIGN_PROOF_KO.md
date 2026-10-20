# RCC-Scope / DistanceGuard: 정확성 계약과 직접 증명

## 범위
불변 directed unweighted multigraph, 한 source에 대한 모든 정점의 정확한 최단거리 배열(미도달=-1). 경로 수, 모든 predecessor, 가중치, 방문 순서, 모든 edge callback의 보존은 요구하지 않는다. 실제 구현은 CPU 단일 소유자 방식이다. 현재 GPU·동시 reader/writer 구현이 아니다.

원본 graph는 `shared_ptr<const Graph>`로 고정한다. reverse의 graph 객체 identity가 정확히 같아야 한다. 같은 정수 version이라도 다른 graph 객체의 cache를 공유하지 않는다. 출력은 다음 요청 전까지만 빌려 쓰는 참조이며 benchmark는 매 요청 전체 배열을 복사해 반환 수명을 고정했다.

## 1. 완료된 BFS의 범위는 닫혀 있다
이전 BFS 시작점 r에서 정확히 도달한 집합 R=Reach(r)를 얻었다고 하자. u∈R이고 (u,v)∈E이면 r→u→v이므로 v∈R이다. 따라서 R 밖으로 나가는 간선은 없다. 단, 밖에서 R 안으로 들어오는 간선은 있을 수 있다.

새 시작점 s∈R이면 Reach(s)⊆R이다. 이에 따라 다음을 안전하게 할 수 있다.
- 이전 RCC: 발견 개수가 |R|에 도달하면 종료.
- 새 Scope: Pull에서 R 밖의 목적지 정점은 아예 검사하지 않음.
- 새 regional RIE: sum(global indegree(v), v∈R이고 아직 미발견)이 0이면 종료.

RCC의 상한만 있는 TABLE은 R의 실제 원소를 알려주지 않는다. Scope는 실제 membership과 열거 가능한 정점 목록을 따로 보유한다. 둘을 같은 기능/동일 저장비라고 하지 않는다.

## 2. Regional RIE에는 전역 indegree를 사용
R은 outgoing-closed일 뿐 incoming-closed가 아니다. 따라서 sum(outdegree[R])로 시작하고 발견할 때 global indegree를 빼면 언더플로/잘못된 종료가 가능하다. 구현은 `sum(indegree(v), v∈R)`를 정확히 계산하고 같은 indegree를 빼므로 음수가 되지 않는다.

미발견 정점 v∈R로 들어오는 간선 수가 모두 0이면, s에서 더 도달할 미발견 정점은 없다. 이 조건은 충분조건이며 필요조건은 아니다.

## 3. 발견한 정점 목록과 frontier 버퍼는 다르다
원본 Direction의 두 queue는 현재/다음 frontier만 보관한다. 이를 완료 집합이라고 재사용하지 않는다. Scope의 새 certificate는 완료 distance[n]을 스캔하여 membership, 정점 목록, incoming sum을 만든다. 준비 비용과 임시 old+new payload를 기록한다.

현재 source가 기존 범위에 속하고, 새 도달 정점 개수가 기존 범위 크기와 같으면 두 집합은 동일하다. 이 경우 이미 있는 certificate를 유지한다. 더 작은 집합이면 완료 후 교체한다. 도달 범위가 전체 graph라면 Scope는 불필요한 전체 목록을 새로 만들지 않는다.

## 4. 공간 범위만으로 부족해서 만든 DistanceGuard
이전 완료 BFS 거리 d_r를 보유하며 s가 r에서 도달 가능해야 한다.

새 BFS의 현재 level을 l이라고 하자. 다음 level l+1에서 발견될 수 있는 v는 반드시 다음을 만족한다.

`d_r(v) <= d_r(s) + l + 1`

증명: 길이 d_r(s)의 r→s 경로와 길이 l+1의 s→v 경로를 잇는다. 최단거리 d_r(v)는 이 경로 길이보다 클 수 없다. 이 부등식을 어기는 v는 이번 level에서만 보류한다. 영구 미도달로 확정하지 않는다.

더 강한 구현은 현재 frontier F_l을 사용한다.

`d_r(v) <= 1 + max(d_r(u) for u in F_l)`

각 실제 간선 (u,v)에 대해 d_r(v)<=d_r(u)+1이기 때문이다. 기존 BFS의 삼각부등식으로 max(d_r(u))<=d_r(s)+l이므로 이 frontier bound는 source-radius bound보다 약하지 않다.

유한한 old distance가 없는 v는 s∈R일 때 영구적으로 범위 밖이다. 다만 이번 시간적 horizon 안에 있는 정점 수를 종료 상한으로 사용하면 안 된다. 이후 level에서 범위가 넓어진다.

## 5. 정확한 결과가 보존되는 이유
각 level에서 현재 frontier와 연결된 미방문 정점만 depth+1로 발견한다. Scope와 DistanceGuard는 이 연결이 불가능하다는 증거가 있는 목적지 후보만 제거한다. 실제 발견되는 정점과 frontier는 기존 Direction+RIE+같은 cardinal bound와 일치한다. alpha=15/beta=24의 정책을 그대로 둔 guard 버전은 level 수와 방향도 동일하다. `SCOPE_LOCAL`은 정책 입력을 바꾸므로 이 마지막 동등성은 주장하지 않는다.

## 6. 실패 안전성
완료되지 않은 검색, 예외/중단 결과는 새 certificate로 공개하지 않는다. 기존 유효 certificate는 유지한다. source 범위/graph identity 불일치는 거부한다. certificate payload budget 또는 주입된 할당 실패에서는 이미 완료된 정답을 반환하고 준비만 생략한다. 과거 immutable snapshot의 reader는 기존 객체를 계속 소유할 수 있다.

예산은 CPU 배열 payload 회계다. allocator header, process RSS, CUDA memory, 외부 reader가 장기간 붙잡는 모든 과거 snapshot까지 포함한 전역 hard limit은 아니다. compact pending-list는 작업공간이며, 그 할당이 불가능하면 C++ allocation 오류가 발생할 수 있다. `Domain`/`direction()`은 검증된 certificate/WCC만 전달하는 내부 trusted helper이고 임의의 위조 목록을 검증하는 보안 API가 아니다.

## 7. 직접 보존한 반례
`results/COUNTEREXAMPLES.json` 및 `tools/verify_guards.py`:
1. 0→1→2의 부분 방문 {0,1}을 closure로 사용하면 2를 누락.
2. R={1,2}, 0→1→2에서 outgoing[R]=1, incoming[R]=2.
3. frontier old-distance의 MIN 대신 MAX가 필요함. MIN은 실제 다음 정점을 제외한다.
4. 이번 level에서 도달 불가능한 v를 영구 미도달로 표시하면 이후 정답이 깨짐.

이러한 충분조건/삼각부등식 자체의 학술적 최초성을 주장하지 않는다.
