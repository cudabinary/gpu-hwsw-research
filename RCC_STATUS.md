# RCC status

현재 단계: **독립 SW 검증 지속 / PAPER_CANDIDATE 아님**.

기능: 현재 CPU RCC TABLE/LAST를 API1.0.0으로 교체 가능하게 감싼 모듈과 baseline 대체 구현이 있다. API 호환성은 실제 동일 MAIN 바이너리 교체로 검사한다. `results/COMPATIBILITY.json`을 권위 있는 새 검사 결과로 읽는다. 이전 수치와 합산하여 새 독립 실험 횟수를 부풀리지 않는다.

성능: LJ q32 Push+RCC가 Push+EARLY_N 대비 약20% 감소했으나 원본 OLD_P2 전체 service 비교가 누락됐다. strongest 전체 승자 UNKNOWN. Direction+RIE 뒤 RCC 추가 작업 생략0은 유지된다. 새 어댑터는 진단 계수와 추가 복사 비용을 가지며 성능을 재측정하지 않았다.

GPU: 역사적 pilot36 BFS+12취소 PASS는 재검증했다. 새 API CUDA 구현/실제 교체 테스트는 미완료. GPU 호환 버전으로 선언 금지.

다음: OLD_P2 전체비용 공정 비교 → 다양한 graph/요청 조건의 실효성 → 강한 공개 baseline/선행연구 감사. 제한된 증거로 논문화·HW 필요성을 선언하지 않는다.

의존성: frozen builder/Direction/bridge 원본 및 g++/Python, CUDA13.3 정적 도구. unresolved: P2 baseline gap, adapter 비용, GPU API backend, 데이터셋 일반성, 신규성.
