# 음성 결과와 실패/한계

원시 시간 이상치와 승패를 삭제하지 않았다. consumer와 service는 각각 21개 짝만 있다.
통계적 유의성, 비열등성, 1% 간섭을 선언하지 않는다.
새 source 순서는 결과를 보고 재선택하지 않았고 original/holdout을 새 미지 데이터로 표현하지 않는다.
현재 서비스는 사전 지정 original만 실행했다. 다른 일정의 전체 서비스 일반성은 UNKNOWN이다.

LJ와 relabel의 RIE 이후 RCC 추가 일이 0인 조건은 결합을 중단했다.
단절 SCC 합성의 큰 RCC 이득을 실제 그래프 일반 성능으로 확대하지 않는다.
WCC로 같은 크기 상한을 얻을 수 있는 합성에서는 reachability 정보의 신규성을 주장하지 않는다.
WCC 전처리와 n개 TABLE 초기화/갱신, LAST_RESULT_REUSE로 단순 중복 source 효과를 드러냈다.
DO_RIE_RCC 경로는 어느 fixture에서도 고정 service gate를 모두 통과하지 못했다.

새 CPU/CUDA 컴파일·정확성 실행은 성공했다. CPU 컴파일에는 줄 배치에 관한 warning 한 건이 있으며
두 독립 if문의 의미를 바꾸지 않는다. 성능 측정 후 그 소스를 다시 수정/컴파일하지 않았다.
새 sanitizer는 실행하지 않았다. CPU PASS / GPU 파일럿 PASS / sanitizer 미실행을 구별한다.

GPU 실행 전 실제 문제를 별도 기록했다:
- 최초 GPU 엔진 counter sample 오류로 CUDA launch 0회 상태에서 보류했다.
- 추가 sandbox 진단은 카운터 object 접근에 실패했다. native 권한의 별도 진단에서 NVIDIA sample 806개 status 0을 확인했다.
  최초 오류의 근본 원인은 확정하지 않았다. 오류 sample을 유효하다고 처리하지 않았다.
- Windows PowerShell 5의 File 실행은 정책상 시작되지 않았다. 시스템 정책을 바꾸지 않고 기존 PowerShell 7을 사용했다.
- PID 1944는 보호 DWM이며 native module 접근이 불가능했다. 이전 승인된 정확한 PID/name/creation identity만 재사용했다.
- PowerShell 7 JSON의 DateTime을 다시 Parse하면서 소수초가 소실되는 새 감시 복사본의 호환 문제를 수정했다.
  DateTime 값을 그대로 UTC로 비교하도록 고쳤으며 matching tolerance·VRAM·온도·watchdog 한도를 완화하지 않았다.
이것들은 CUDA 실패 후 재시도가 아니다. 실제 커널 파일럿은 한 캠페인만 수행했다.

일반 GUI 컨텍스트는 고정 PID·생성시각·모듈·GPU engine으로 감시했다.
보호 OS 컨텍스트는 modules 대신 고정 CIM identity와 engine을 감시한 예외다.
따라서 모든 GUI의 셰이더가 전혀 없다고 보장하지 않는다. 측정 GPU 결과를 전용 headless 환경과 동일시하지 않는다.
