# RCC status

최신(2026-10-21): **DistanceGuard API1.0.0 실험 호환성 PASS / 기본 RCC 통합 HOLD**. `research/DG_API_RESULTS.md`와 `results/dg_api_20261021/`가 이번 후보 API 검증의 근거다. 기존 MAIN SHA `d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e`를 변경·재빌드하지 않고 기본 BFS/TABLE/LAST 및 DG4종×ready/deferred 11개 교체 모두 PASS. 전체 서비스 26,880 trials/564,480 배열과 별도 Python 검증 PASS. matched 출력 복사·알고리즘/어댑터 비용·5 session 변동을 분리했다.

유일한 조건부 양성은 합성 oneway_dense/legacy/q32/ready, DG/matched TABLE0.7331 [기술적 bootstrap95% 0.7195–0.7672],37/40승리다. 준비 포함 약1.31 및 unique ready1.3117로 역전된다. Google은 API bound<n 제한으로 필터의 고유 작업 생략이 유지되지 않고, LJ는 matched 생략48,273 probes에도 OLD_P2/RIE보다 느리다. 실제 graph의 강한 고유 전체시간 우위 미확보. 추가 최적화·기본 통합·자동 병합 없음. 새 GPU/유료 자원0. 신규성·독립 논문 기여 미확립 판정 유지.

아래는 이전 OLD_P2/패키지 감사 체크포인트 기록이다. 그 시점의 후보 API 미구현·비용 UNKNOWN은 위 새 실험으로 갱신됐으며, 이전 자료와 측정 경계는 그대로 보존한다.

현재 단계: **독립 SW 검증 지속 / PAPER_CANDIDATE 아님**.

기능: 현재 CPU RCC TABLE/LAST를 API1.0.0으로 교체 가능하게 감싼 모듈과 baseline 대체 구현이 있다. API 호환성은 실제 동일 MAIN 바이너리 교체로 검사한다. `results/COMPATIBILITY.json`을 권위 있는 새 검사 결과로 읽는다. 이전 수치와 합산하여 새 독립 실험 횟수를 부풀리지 않는다.

성능: 2026-10-21 고정 OLD_P2 보완 실험을 완료했다. LJ original/relabel, q8/q32, 3 CPU 프로세스×7라운드×반대 순서 2 sweep, 672 trials의 전체 거리 배열 14,112개가 일치했다. RCC TABLE은 PUSH_N 및 OLD_P2 deferred 대비 네 조건에서 사전 gate를 통과했다. original의 OLD_P2 ready 대비 RCC/P2는 q8=1.3045, q32=1.0667로 RCC 우위가 아니다. q8은 ready P2의 guarded win이며 q32는 P2 관측 선두지만 3 session 모두 5% 우위 gate를 충족하지 못했다. relabel에서는 RCC가 ready P2 대비도 gate를 통과했다. 조건별 승자는 다르며 보편적 strongest 승자는 UNKNOWN이다. 상세/원시 근거는 `research/OLD_P2_SERVICE_RESULTS.md`, `results/old_p2_service_20261021/`.

비용: 원본 service 경계 외에 ready reverse 준비·검증·해제·연속 lifecycle 비용을 함께 보존했다. 이미 준비된 reverse의 과거 비용을 ready 서비스에 다시 청구하지 않는다. 새 API 어댑터는 진단 계수와 추가 복사 비용을 가지며 이 어댑터의 성능은 아직 미측정이다. Direction+RIE 뒤 기존 RCC 추가 작업 생략0이라는 역사적 관찰은 새 P2 측정으로 변경하지 않는다.

GPU: 역사적 pilot36 BFS+12취소 PASS는 재검증했다. 새 API CUDA 구현/실제 교체 테스트는 미완료. GPU 호환 버전으로 선언 금지.

확장 감사 완료: `research/SCOPE_DISTANCE_AUDIT_RESULTS.md`. ZIP CRC/92개 manifest bytes/SHA PASS, 재빌드 정확성·독립 Python·4개 반례·기전 재현 PASS. 16개 policy, cold/ready·q8/q32·5개 graph×2 source 순서의 고정 3프로세스×7round×mirror 비교 26,880 trials/564,480 전체 배열 PASS. DistanceGuard는 기존 RIE+RCC TABLE 이후 Google/LJ에서 추가 edge probe를 생략했지만 실제 파생 입력의 강한 전체시간 우위는 확보하지 못했다. Scope는 모든 고정 대조군 대비 gate 통과 조건0, Distance FRONTIER는 합성 oneway_dense/legacy/q32/ready 하나에서만 통과했다. 이 조건도 cold/준비비 포함 또는 unique 요청에서는 RCC TABLE보다 느리다.

통합: 기본 RCC 통합 없음. 기존 API1.0.0 동일 MAIN 바이너리 교체를 재실행해 PASS. 전달 helper는 공통 API plugin을 구현하지 않아 후보 API 호환성은 NOT_IMPLEMENTED_NOT_VERIFIED다. 기본 모듈의 성공을 후보에 전이하지 않는다. 새 GPU·유료 자원0. 원본 ZIP/추출본·OLD_P2 commit을 보존했다.

다음: 두 확장은 독립 실험 후보로 보존한다. 실제 workload/graph holdout·강한 공개 구현·저렴한 사전 적용 규칙/선택 비용·후보 API adapter 검증이 없는 상태에서 기본 활성화·논문 후보 승격·GPU/HW 필요성을 선언하지 않는다. `research/SCOPE_DISTANCE_NOVELTY_AUDIT.md`의 1차 출처 대조에서도 최초성/독립 논문 기여는 미확립이다.

의존성: frozen builder/Direction/bridge 원본 및 g++/Python, CUDA13.3 정적 도구. unresolved: API adapter 비용/후보 plugin, GPU API backend, 데이터셋 일반성, 신규성. OLD_P2 누락 및 전달 패키지의 한정 CPU 독립 감사는 완료했다.
