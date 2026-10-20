# RCC 신규성 감사 상태

최신 전달 패키지 감사: `research/SCOPE_DISTANCE_NOVELTY_AUDIT.md` 및 `research/SCOPE_DISTANCE_AUDIT_RESULTS.md`. RCC-Scope와 DistanceGuard의 정확한 추가 기전·조건부 합성 witness는 재현했으나 실제 파생 입력의 강한 전체 서비스 우위·학술적 최초성·독립 논문 기여는 미확립이다. ALT/PLL/DO-BFS/GAP/O'Reach/SlimSell 1차 출처를 대조했다. 기본 통합 없음. 아래의 미개봉 기술은 이전 OLD_P2 체크포인트 당시 상태다.

이번 작업은 모듈화·호환성·연구 환경 관리이며 신규 알고리즘 기여가 아니다. 기존 Direction-Optimizing BFS, RIE 종료, RCC reachability 상한, TABLE/LAST 캐시를 보존한다.

현재 증거는 일부 CPU 비용 감소와 정확한 종료 인증의 구현이다. 2026-10-21 OLD_P2 동일 service 비교 누락을 고정 조건에서 보완했지만 original ready P2 대비 RCC 우위는 성립하지 않았다. SCC/WCC 및 도달성 인덱스/기존 방문 결과 재사용과의 구분, 공개 강한 구현, 다양한 실제 그래프, cold/warm 비용 및 통계적 불확실성 비교가 더 필요하다.

`evidence/previous/NOVELTY_SCOPE.md`의 범위를 승계한다. 이번 분리 단계에서 새 문헌 검색이나 완결된 선행연구 감사를 수행하지 않았다. 따라서 미검증 신규성 주장을 추가하지 않는다.

## 2026-10-21 한정 1차 출처 확인

이번 후속 작업에서는 아래 1차 출처를 확인했다. 완결된 문헌조사나 구현 간 성능 비교를 대신하지 않는다.

- Beamer/Asanovic/Patterson, [Direction-Optimizing Breadth-First Search, SC2012](https://people.eecs.berkeley.edu/~krste/papers/beamer-sc2012.pdf): frontier에 따라 top-down/bottom-up을 전환하여 검사량을 줄이는 기존 방법이다. frozen P2의 계열상 강한 대조군이며, 이번 측정에서 original ready P2가 RCC의 보편 우위 주장을 반박한다. frozen P2를 저자 공개 구현 전체와 동일시하지 않는다.
- Hanauer/Schulz/Trummer, [O'Reach, SEA2021](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2021.13), [저자 공개 코드](https://github.com/o-reach/O-Reach): 선형 크기 인덱스로 많은 정적 그래프 s-to-t 도달성 질의를 지원하며 구축/질의/메모리 비용을 다룬다. Boolean 도달성 질의는 owned 전체 거리 배열 계약과 다르다. 따라서 논문의 query time을 RCC 전체 BFS 분모로 쓰지 않았다. 향후 영역 제한/도달성 인증의 선행기술 감사에 포함해야 한다는 판단은 이 계약 비교에서 도출한 추론이다.
- Akiba/Iwata/Yoshida, [Pruned Landmark Labeling, SIGMOD2013](https://arxiv.org/abs/1304.4661): 기존 거리 label을 사용한 BFS pruning으로 정확한 최단거리 질의를 지원한다. 새로운 DistanceGuard 패키지를 읽지 않은 현재 두 방법의 동일성이나 차별성을 판정할 수 없다. 후속 감사에서는 전처리·label 유지·전체 n개 거리 출력 비용과 정확성 조건을 명시적으로 비교해야 한다.

현재 RCC의 포함관계 `s in Reach(r) => Reach(s) subset Reach(r)`는 경로 연결로 직접 증명되는 성질이다. 정확한 완료 집합에서 얻은 상한에 distinct seen이 도달하면 도달 집합을 모두 찾았다는 인증은 타당하지만, 이 수학적 성질·테스트 PASS·일부 CPU 시간 감소만으로 학술적 최초성이나 독립 논문 기여가 성립하지 않는다. 같은 immutable graph/완료 인증/소유 출력 조건을 유지해야 한다.

판정: **CONTINUE_SW / NOVELTY_NOT_ESTABLISHED / PAPER_CANDIDATE 아님**. 새 두 모듈은 이 체크포인트에서 미개봉·미실행이며, 내용이나 반례를 추측해 재구현하지 않았다. 패키지의 독립 감사와 기존 RCC·OLD_P2·Direction+RIE 등 동일 계약 비교 이후에만 고유 이득과 선택적 통합을 평가한다.

도달 범위로 다음 검사 영역을 줄이는 후보는 DISCOVERY다. 조건·정확성·고유한 생략·상태 유지 비용·반례·strong baseline 비교를 먼저 확보한다. 만족하지 않으면 VALIDATED/PAPER_CANDIDATE로 올리지 않는다. 논문화 브랜치와 투고는 사용자 승인 후다.
