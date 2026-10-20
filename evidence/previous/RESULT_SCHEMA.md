# 결과 해석 규칙

- `results/gate_*.csv`: 3 CPU 프로세스 × 7회. `ns`는 전체 거리 반환까지의 resident 소비자 batch. `priming_ns`는 warm certificate를 만든 과거 3요청 비용이다. `validation_ns`/`release_ns`는 별도다.
- `CPU_CERTIFICATE_HISTORY_COST.csv`: 과거 priming+현재 소비 시간의 **측정 성분 합**이다. reverse 구축/전송을 포함한 GPU 서비스 시간으로 해석하지 않는다.
- `results/work.csv`: 독립 계측 template의 **cold certificate** 작업량. warm 타이밍의 작업량을 측정한 것이 아니다. 최종 incremental CSV의 warm work 칸은 UNKNOWN이다.
- `remaining`/GPU `remaining_in`: 새 Direction 경로에서만 정확 indegree 합이다. Push와 old diagnostic에서 0은 미계측/미사용 값이며 RIE=0의 증거가 아니다.
- 새 CPU `Output::count()`는 certificate 경로에서 정확 도달 수이다. 원본 P0/P2 연결용 legacy 경로는 전체 거리만 보장하며 `count()==0`을 UNKNOWN sentinel로 둔다. n>0에서 실제 완료 BFS의 도달 수는 최소1이다. Legacy 결과를 RCC certificate로 가져오는 API는 없다.
- `rows`는 새 Push에서 실제 확장한 source-row 수. Direction/legacy의 0은 그 별도 계수 미구현이다. `levels`는 새 Push/Direction에서 실제 확장한 레벨이며 원본 bridge Push의 0과 구별한다.
- `CPU_COLD_WARM_SERVICE.csv`: graph resident, reverse cold/deferred/concurrent 또는 과거 ready. certificate는 이번 A 결과로 시작한다. 별도 과거 certificate warm 서비스가 아니라 reverse 가용 상태를 구분한다.
- `median_paired_ratio`는 동일 process/round의 비율들을 취한 중앙값이다. 두 전체 중앙값의 단순 나눗셈이 아니다. wins는 엄격한 ratio<1 횟수이며 유의성 검정 결과가 아니다.
- `CPU_STRONG_SERVICE_COMPARISON.csv`: **실제로 서비스에서 측정한 후보 중** 비-RCC 최강이다. 원본 P2 서비스가 누락되어 전역 최강을 보장하지 않는다.
- `payload_upper_bytes`는 배열 payload의 보수적 계산치다. RSS는 실제 worker 프로세스 고수위이며 preload한 fixture와 oracle도 포함한다. 두 값은 다른 측정 경계다.
- GPU `stream_interval_ms`: stream event의 간격. host 제출/동기화 간격도 포함하므로 kernel busy time이 아니다. `wall_ms`에 반환 복사·TABLE publication은 포함하고 독립 oracle 검증은 분리했다.
- GPU 원시 stdout의 첫 요청 비용, source 사이의 취소 검사, 별도 validation 간격을 숨기지 않는다. GPU q32 전체 서비스/반복 성능/Plan A 1% 간섭 판정은 UNKNOWN이다.
