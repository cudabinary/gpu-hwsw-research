# 실제 통합 구현

`frozen/consumer`의 Graph, reverse Builder, P0/P2 소스 3개는 원본과 동일하다.
`frozen/bridge/stop_bridge.hpp`도 보존했다. 새 `include/adapter.hpp`는 Direction 실행에
감사한 bridge의 정확한 remaining-indegree / bitmap / alpha=15, beta=24 코드를 사용한다.
Push는 FIFO를 유지하며 distinct 발견 수가 n 또는 과거 증거 상한에 도달한 후 안전한 행 경계에서 멈춘다.

17개 비교 경로: OLD_P0, OLD_P2, PUSH_N, DO_N, DO_RIE, PUSH_RCC_LAST, PUSH_RCC_TABLE,
DO_RIE_RCC_LAST, DO_RIE_RCC_TABLE, PUSH_TABLE_OFF, DO_RIE_TABLE_OFF, PUSH_LAST_OFF,
DO_RIE_LAST_OFF, PUSH_WCC, LAST_RESULT_REUSE, DO_N_RCC_TABLE, DO_N_TABLE_OFF.
OFF는 같은 TABLE/LAST 유지 작업을 수행하며 RCC 종료에만 쓰지 않는다.
WCC는 제공된 union-find 방법을 동일 그래프에 적용한다. parent/size/bound 12n 바이트와 전체 CSR 스캔을 부담한다.

새 결과 계약은 `shared_ptr<const Output>`이며 전체 거리 배열을 복사해 돌려준다.
다음 실행이나 Executor 파괴 뒤에도 유효하다. LAST는 이 결과의 소유권을 유지하고 TABLE은 완료 distance[n]을 스캔한다.
기존 bridge LAST scratch swap의 다음 호출까지인 borrowed-reference 계약과 구별한다.
LAST_RESULT_REUSE만 같은 source의 불변 결과를 그대로 돌려줄 수 있다. 그 별칭과 메모리를 별도 계수한다.

생략되는 것은 탐색의 남은 행/레벨과 그 검사 비용이다. 최종 reverse가 필요한 Direction에서는
COUNT/scan/scatter를 생략하지 않는다. Push+RCC는 reverse 자체가 필요 없어서 그 전체 구축·보관 비용을 피한다.
RIE가 이미 생략한 작업을 RCC의 기여로 중복 계상하지 않는다.
