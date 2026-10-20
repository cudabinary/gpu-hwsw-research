# 원본 / bridge 대조

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


외부 다운로드가 실패한 뒤 동일 파일명·크기의 로컬 첨부 사본을 사용했다.
실제 7,431,945바이트 ZIP의 SHA-256은 b2c6f4d49d0af97e11125c1588e444f85e6255ecf1b54a165ba4920d004b963b.
CRC 및 경로 탈출/중복 이름/링크 검사를 통과했다. outer manifest 73개와 nested ZIP manifest를 재검사했다.
audit/INPUT_FREEZE.json에 각 nested ZIP의 실제 SHA·검사 개수가 있다.

Consumer 원본 vendor 3개는 로컬 원본과 바이트가 같다. 원본 manifest 197개 파일을 완료 시 재검사했다.
이번 benchmark 당시의 pin 22개도 그대로다.
기존 Consumer-first LJ q32 순차 0.840713 / 병행 0.865155 성과를 유지한다.
이번 강한 Push_N baseline, owned output, certificate publication 계약의 결과와 수치를 직접 혼합하지 않는다.

bridge raw 기록과 새 구현의 공통 9개 모드·18개 graph/schedule에서 26,730개 필드를 대조했다.
불일치 0개. 별도 Python으로 확인된 새 전체 배열과 기존 export 864개도 동일했다.
이는 제공된 과거 C++ 실행을 다시 했다는 뜻은 아니다. 과거 87,552건과 새 검사 건수는 별도다.

확인된 한계/차이:
- bridge Push의 levels=0은 계측 미구현 값이며 실제 0레벨 탐색이 아니다. 새 Push는 expanded rows/실행 level을 계수한다.
- 기존 bridge LAST 반환값은 다음 호출까지의 scratch/buffer 참조다. 새 모듈은 독립 소유 전체 배열 반환 비용을 포함한다.
- bridge cache는 예산/할당 실패 fallback이 없다. 새 adapter에서 추가했다.
- RCC 원본 Direction의 remaining 정의는 Codex의 정확 indegree 합과 다르므로 타이밍을 같은 backend처럼 섞지 않는다.
- original/holdout은 이미 본 일정이다. 새 순서 한 개만 seed=20261021로 사전 고정했다.
- relabel original은 vertex mapping을 따르지만 holdout의 숫자 source는 동일 relabel vertex를 의미하지 않는다.
- 제공된 EPYC/g++14.2 타이밍과 이번 i5-14500/WSL/g++15.2 타이밍은 직접 비율 계산하지 않는다.

최초 ZIP 읽기 도구는 중복 README 검색에서 멈췄지만 import/CRC는 완료돼 있었다.
정확한 root 경로로 요구된 세 문서를 순서대로 읽었다. 이 준비 도구 오류를 실험 실패/성공 건수에 섞지 않는다.
