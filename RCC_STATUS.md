# RCC status

현재 단계: **독립 SW 검증 지속 / PAPER_CANDIDATE 아님**.

기능: 현재 CPU RCC TABLE/LAST를 API1.0.0으로 교체 가능하게 감싼 모듈과 baseline 대체 구현이 있다. API 호환성은 실제 동일 MAIN 바이너리 교체로 검사한다. `results/COMPATIBILITY.json`을 권위 있는 새 검사 결과로 읽는다. 이전 수치와 합산하여 새 독립 실험 횟수를 부풀리지 않는다.

성능: 2026-10-21 고정 OLD_P2 보완 실험을 완료했다. LJ original/relabel, q8/q32, 3 CPU 프로세스×7라운드×반대 순서 2 sweep, 672 trials의 전체 거리 배열 14,112개가 일치했다. RCC TABLE은 PUSH_N 및 OLD_P2 deferred 대비 네 조건에서 사전 gate를 통과했다. original의 OLD_P2 ready 대비 RCC/P2는 q8=1.3045, q32=1.0667로 RCC 우위가 아니다. q8은 ready P2의 guarded win이며 q32는 P2 관측 선두지만 3 session 모두 5% 우위 gate를 충족하지 못했다. relabel에서는 RCC가 ready P2 대비도 gate를 통과했다. 조건별 승자는 다르며 보편적 strongest 승자는 UNKNOWN이다. 상세/원시 근거는 `research/OLD_P2_SERVICE_RESULTS.md`, `results/old_p2_service_20261021/`.

비용: 원본 service 경계 외에 ready reverse 준비·검증·해제·연속 lifecycle 비용을 함께 보존했다. 이미 준비된 reverse의 과거 비용을 ready 서비스에 다시 청구하지 않는다. 새 API 어댑터는 진단 계수와 추가 복사 비용을 가지며 이 어댑터의 성능은 아직 미측정이다. Direction+RIE 뒤 기존 RCC 추가 작업 생략0이라는 역사적 관찰은 새 P2 측정으로 변경하지 않는다.

GPU: 역사적 pilot36 BFS+12취소 PASS는 재검증했다. 새 API CUDA 구현/실제 교체 테스트는 미완료. GPU 호환 버전으로 선언 금지.

다음: 이번 OLD_P2 결과·커밋·Push를 먼저 보고한 뒤 전달된 RCC-Scope·DistanceGuard 패키지를 독립 감사한다. 이 체크포인트에서는 ZIP 미개봉·미실행이며 추측 구현/기본 RCC 통합 없음. 다양한 graph/요청 조건, 강한 공개 baseline, API 어댑터 비용, 선행연구 감사가 계속 필요하다. 제한된 증거로 논문화·HW 필요성을 선언하지 않는다.

의존성: frozen builder/Direction/bridge 원본 및 g++/Python, CUDA13.3 정적 도구. unresolved: adapter 비용, GPU API backend, 데이터셋 일반성, 신규성, 새 두 모듈의 독립 감사. OLD_P2 누락은 위 한정 조건에서 해소했다.
