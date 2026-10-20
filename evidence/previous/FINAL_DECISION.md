# 최종 판정: 선택적 CONTINUE_SW

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


1. **유효한 Direction 성과는 강한 기준선에서도 남는다.**
LJ original의 resident DO_RIE / PUSH_N 짝 중앙값은 약0.759이며,
준비 포함 q32 순차 DO_RIE 서비스는 0.8941배였다.
그래프/일정 전반의 무조건적 우위는 아니다. 순차가 병행보다 유리한 결과를 그대로 유지한다.

2. **RCC의 추가 생략은 소비자에 따라 다르다.**
LJ에서는 RIE 이후 RCC의 추가 edge/vertex-test 생략이 0이다. 결합을 중단했다.
단절 SCC에서는 RCC가 Direction+RIE 이후에도 일을 생략하지만 Push+RCC 및 WCC라는 더 강한 설명/대조가 있다.
reverse 없는 Push에서 RCC는 EARLY_N이 보장하지 못하는 과거 도달 크기 상한으로 추가 행을 생략한다.
LJ의 도달 집합이 n보다 조금 작은 경우에도 마지막 큰 행/레벨을 처리할 필요가 없어질 수 있다.
이는 실제 source 변경/행 순서와 종료 경계에 의존하며 신규 HW를 필요로 하지 않는다.

3. **전체 비용의 승자는 reverse의 가용 상태에 따라 달라진다.**
LJ cold q32 Push+RCC_TABLE은 0.7999배이며 reverse 구축을 피한다.
완전 reverse가 이미 resident라면 ready DO_RIE가 다른 강한 경로다.
q1/q2/q8 및 q0의 비용은 CPU_COLD_WARM_SERVICE.csv에 보존했으며 q32 성과를 임의로 확대하지 않는다.
WCC/단순 결과 재사용 포함 최강 measured 비-RCC 경로와의 비교도 제공한다.

**최종 질문에 대한 답:** 이 계약에서는 미리 수행한 완료 BFS가 다음 탐색의 남은 행/레벨을 실제로 없앨 수 있다.
그러나 RIE로 이미 사라진 일을 RCC가 다시 없앨 수는 없다. 필요한 경우 reverse 자체를 만들지 않는 쪽이 더 저렴하다.
새 builder·부분 인덱스·HW 엔진을 만들 이유는 이 결과에서 나오지 않는다.

CPU 실용 개선: 특정 입력/일정/q에서 확인. 독립 신규성: 미입증. 새 HW 필요성: 미확정.
실제 GPU 정확성: 36 BFS/12취소 PASS. GPU 성능 성공·Plan A 간섭≤1%·GPU q32 전체 개선: UNKNOWN.
이번 GPU 결과는 CPU 근거를 실제 장치의 정확성까지 확장했으며, 반복 계측 없는 가속 결론은 내리지 않는다.
