# RCC / RIE Consumer 통합 — CPU 결과와 실제 GPU 파일럿

## 최종 강한 대조군 감사 — 반드시 함께 읽을 한계

원본 OLD_P2도 합법적인 비-RCC 기준선이다. 새 RIE가 항상 가장 강하다고 볼 수 없다.
LJ original의 상주 소비자에서 OLD_P2 / PUSH_N은 0.7263배였고,
DO_RIE / OLD_P2의 짝 중앙값은 **1.0505배**였다.
같은 adapter의 DO_N에 비해 RIE가 일을 줄여도, frozen P2보다 최종 시간이 짧다는 뜻은 아니다.
정확 discovered count/종료 검사, bridge의 validation/control 구조와 코드 생성 비용이 다르며,
그 각각의 시간 기여를 분리 측정하지 않았으므로 특정 한 연산을 원인으로 단정하지 않는다.

초기 서비스 후보 목록에서 OLD_P0/OLD_P2를 누락했다. `config/service_modes.txt`와 초기 집계는
그대로 보존했고, 추가 CPU benchmark는 실행하지 않았다. CPU_INCREMENTAL_VALUE.csv는 기존 raw만
재집계하여 OLD_P0/OLD_P2까지 포함한 최강 resident 대조군으로 수정했다.
초기 파일은 results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv에 보존했다.

따라서 Push+RCC_TABLE의 cold q32 0.7999배(PUSH_N 대비),
0.8999배(이번에 서비스에서 측정한 순차 DO_RIE 대비)는 실제 측정 범위의 성과다.
**동일 owned-output 계약의 원본 P2 전체 서비스까지 포함한 최종 승자는 UNKNOWN**이다.
과거 P2의 0.840713 수치를 이번 결과에 섞어 그 빈칸을 메우지 않는다.
최소 추가 증거는 frozen P2의 순차/ready 서비스와 Push+RCC_TABLE을 동일 출력 계약으로 짝 비교하는 것이다.
이번 3개 CPU 프로세스 × 7회 한도를 초과해서 그 보완 실험을 숨겨 실행하지 않았다.

GPU pilot은 두 후보의 정확성만 확인했으므로 이 CPU 대조군 누락을 보완하지 않는다.
GPU graph-version mismatch/할당 실패/dispatch cap을 실제 오류로 주입하지 않았고,
그 부분은 CPU 검사 또는 정적 guard에 머문다. 실제 GPU의 cancellation/source 교대와 전체 배열 검사는 PASS다.


이번 결론은 **선택적 CONTINUE_SW**다. Direction+RIE와 reverse 없는 Push+RCC는 서로 다른 비용 조건에서 유효하다.
LiveJournal에서 RIE 뒤 RCC의 추가 검사 생략은 **0**이므로 결합 경로는 서비스에 연결하지 않았다.
Node/head/link, 부분 인덱스, builder, HW 엔진을 새로 만들지 않았다.

- 새 CPU: 240,415 전체 거리 비교, 988,173 assertions PASS. 소형 그래프 576개, fixture 요청 15,147개 포함.
- 새 독립 Python: 1,836 배열 / 4,915,788 원소 PASS. 기존 bridge 증거 배열 864개도 대조했다.
- CPU: 고정 3개 프로세스 × 7회; resident 행 19,278개, 서비스 행 4,305개. 임계값 alpha=15, beta=24 고정.
- 실제 RTX 4060 Ti: 12개 프로세스, 전체 거리 BFS 36회와 취소 12회 PASS.
  14.91초, 관측 여유 VRAM 최소 6878MiB, 최고 44°C.
- GPU 커널 232회. 정적 PTX/cubin 및 native owner 링크 PASS. Nsight·sanitizer 0회.

CPU LiveJournal original q32의 A+준비+반환 포함 서비스는 Push+RCC_TABLE 0.7999배,
순차 reverse+Direction+RIE 0.8941배 (각각 강한 Push+EARLY_N 대비).
resident reverse가 이미 있으면 Direction+RIE가 다른 선택이 된다. 준비 비용을 지워서 순위를 비교하지 않는다.
GPU 파일럿은 반복 성능 실험이 아니며 GPU 성능 성공·1% 간섭·HW 필요성을 입증하지 않는다.

읽는 순서: MERGED_CONSUMER_IMPLEMENTATION → CERTIFICATE_CORRECTNESS_AND_LIFETIME →
SOURCE_BASELINE_RECONCILIATION → COST_AND_INTERFERENCE_ANALYSIS → FINAL_DECISION.
CPU_INCREMENTAL_VALUE.csv, CPU_COLD_WARM_SERVICE.csv, CPU_STRONG_SERVICE_COMPARISON.csv와 results/에 원시 기록이 있다.
이 ZIP은 로컬 제출물이다. 외부 업로드를 수행하지 않았다.
