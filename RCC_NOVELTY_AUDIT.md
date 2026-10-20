# RCC 신규성 감사 상태

이번 작업은 모듈화·호환성·연구 환경 관리이며 신규 알고리즘 기여가 아니다. 기존 Direction-Optimizing BFS, RIE 종료, RCC reachability 상한, TABLE/LAST 캐시를 보존한다.

현재 증거는 일부 CPU 비용 감소와 정확한 종료 인증의 구현이다. 최강 service 기준선 OLD_P2가 빠져 있으므로 독자적 우위가 완결되지 않았다. SCC/WCC 및 도달성 인덱스/기존 방문 결과 재사용과의 구분, 공개 강한 구현, 다양한 실제 그래프, cold/warm 비용 및 통계적 불확실성 비교가 더 필요하다.

`evidence/previous/NOVELTY_SCOPE.md`의 범위를 승계한다. 이번 분리 단계에서 새 문헌 검색이나 완결된 선행연구 감사를 수행하지 않았다. 따라서 미검증 신규성 주장을 추가하지 않는다.

도달 범위로 다음 검사 영역을 줄이는 후보는 DISCOVERY다. 조건·정확성·고유한 생략·상태 유지 비용·반례·strong baseline 비교를 먼저 확보한다. 만족하지 않으면 VALIDATED/PAPER_CANDIDATE로 올리지 않는다. 논문화 브랜치와 투고는 사용자 승인 후다.
