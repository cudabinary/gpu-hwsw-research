# 후속 Codex 통합 메모 — 현재 진행 중 작업 변경 지시가 아님

이번 독립 트랙은 두 가지 후보와 반례를 가져왔다. Codex의 기존 Direction+RIE/서비스 통합이 끝난 뒤 필요한 것만 선택해 비교한다. 새 builder, 이벤트 큐 또는 GPU 실행을 시작하라는 승인이 아니다.

1. `ClosureScope`는 완료된 Reach(r)의 실제 membership으로 Pull 목적지 후보를 줄인다. 예전 RCC_TABLE의 count만으로는 같은 목록을 만들 수 없다. prepared reverse 배열/원래 direction alpha,beta를 그대로 사용한다.
2. `DistanceGuard::FRONTIER_MAX`는 직전 완료 BFS 거리 배열 하나(4nB)를 유지하고, 이번 frontier old-distance 최대값+1보다 큰 목적지의 incoming 목록을 읽지 않는다. 이전 결과는 버퍼 swap으로 보존하되 실제 반환 copy/retained memory/수명 비용은 남는다.
3. 지역 범위가 거의 전체인 LiveJournal에서도 두 번째는 RIE 이후 추가 probe를 생략했다. 하지만 old-distance lookup이 더 많아 CPU 시간은 악화됐다. 기본 활성화하지 않는다.
4. 임시 radius 안의 정점 개수를 종료 상한으로 사용하지 않는다. 안전한 완료 종료는 exact count/RIE/closure cardinal bound만 사용한다.
5. 고차수 불가능 후보의 긴 incoming 스캔을 4B label read로 대체하는 구간에만 기대 이득이 있을 수 있다. 이것은 다음 가설이지 GPU 결과가 아니다. per-level saved-probe/extra-label-read/체크 비용을 분리해야 한다.
6. 알고리즘 원리는 landmark/triangle inequality/pruning 선행연구와 겹친다. 새 모듈을 만들었다고 신규성 확정하지 않는다.
7. 직접 도입하려면 기존 source 순서와 새 고정 순서, source 밖 범위, 같은 source 결과 캐시, graph identity, 완료 전 취소, 전체 거리 출력을 같은 backend에서 검증한다.
8. 현재 구현은 CPU 단일 owner. GPU로 옮길 경우 frontier-max reduction, 이전 배열/현재 배열 수명, 정확한 publication, 여분 메모리, reduction 때문에 생기는 동기화 비용이 별도로 발생한다. 새 HW 필요성을 단정하지 않는다.

현재 Codex의 진행 자료/승인/ledger를 덮어쓰지 않는다. 대조군 이득이 작은 입력에서 이 모듈을 강제로 합치지 않는다.
