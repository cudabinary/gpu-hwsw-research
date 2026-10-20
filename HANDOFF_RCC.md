# RCC 독립 연구 인계

## 최신 DistanceGuard API 체크포인트

`research/DG_API_RESULTS.md`를 먼저 읽는다. 사용자 명시 요청으로 기본 RCC와 분리한 API1.0.0 실험 plugin을 구현했다. **MAIN 소스·실행물 수정/재빌드0**. 기존 MAIN에서 기본3종+DG4종×ready/deferred 실제 교체 모두 PASS다. primary 5프로세스×8round×mirror의26,880 trials/564,480 전체 배열, Python2688배열/6544608원소 PASS. 원본 ZIP·기존 Scope/DG202 artifact·OLD_P260 artifact를 commit blob과 현 파일로 확인해 보존했다.

기본 통합은 **HOLD**다. oneway_dense/legacy/q32/ready의 유일한 합성 조건부 gate 양성은 matched TABLE 대비0.7331이나 준비 포함 약1.31/unique ready1.3117로 역전된다. Google/LJ의 고유 강한 전체시간 우위 없음. bound<n API 의미에 따른 fallback과 출력 한 번 복사의 효과를 guard 자체의 효과와 구별한다. 결과를 본 뒤 추가 최적화/실험 반복을 하지 않았다. GPU/유료 자원0. 원시 로그·통계·비용·실행 binary bundle은 `results/dg_api_20261021/`다. 기본 활성화·MAIN 병합·후속 최적화/GPU를 자동 진행하지 않는다. 아래는 이전 체크포인트 당시의 인계 기록이며 그 문서·raw 결과를 덮어쓰지 않았다.

## 시작 위치

- 브랜치: `research/rcc`
- 절대 경로: `C:\Users\정다빈\Documents\Codex\2026-10-20\task\GPU_HW_SW_RESEARCH_20261021\rcc`
- MAIN: 같은 상위 폴더의 `main`, 브랜치 `main`
- 원본 연구: `C:\Users\정다빈\Documents\Codex\2026-10-20\task\TCSC_RCC_RIE_CPU_STATIC_20261021` — 변경 금지
- 원격: `https://github.com/cudabinary/gpu-hwsw-research.git`, 비공개

`START_RCC_CODEX.md`, `RCC_STATUS.md`, `RCC_INTEGRATION_CONTRACT.md`, `RCC_NOVELTY_AUDIT.md`, `evidence/previous/SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md` 순서로 읽는다. 새 채팅은 자동으로 시작하지 않았다.

## 문제·구현

이전 완료 BFS의 도달 집합 R 안에 source s가 있으면 Reach(s)⊆R이라는 상한을 사용한다. TABLE은 정점별 도달 개수 상한을, LAST는 직전 owned 결과를 유지한다. 정확한 완료 BFS에서만 상태를 갱신하며 부분 탐색은 인증으로 공개하지 않는다. source의 도달 상한에 distinct seen이 도달하면 안전한 행/레벨 경계에서 종료한다.

현재 코드: `vendor/rcc_20261021/include/adapter.hpp`, `frozen/bridge/stop_bridge.hpp`, 원본 RCC `frozen/rcc/`. Direction/Builder는 `frozen/consumer/`. CUDA kernel/Windows host owner는 `vendor/rcc_20261021/cuda/`. vendored 파일은 SHA로 고정한다. 새 공통 모듈은 `src/cpu_module.cpp`; 기존 알고리즘을 감싼 것으로 새 RCC 알고리즘이 아니다.

## 검증된 상태와 반증

- 이전 CPU: 전체 배열 비교 240,415건, assertion 988,173건. 모두 독립 BFS 실행 횟수라는 뜻은 아니다.
- 독립 Python: 1,836 배열, 4,915,788 원소.
- 이전 GPU: 실제 stdout/receipt/소스·바이너리·입력 SHA 대조 완료. 12프로세스, BFS36, 취소12, kernel232, 14.907초, 최고44°C, 최저 여유6878MiB. GPU 성능 우위·공통 API 호환성 증거가 아니다.
- LJ q32 Push+RCC TABLE / Push+EARLY_N 전체 서비스 비율 약0.79991.
- Direction+RIE 뒤 RCC의 추가 edge/vertex 검사 생략은 해당 LJ 조건에서0/0.
- 최초 분리 시 원본 P2의 동일 owned-output 전체 service 비교가 누락됐다. 2026-10-21 보완 결과는 아래 후속 과제 갱신과 `research/OLD_P2_SERVICE_RESULTS.md`를 참조한다. 원본 P2는 resident 및 original ready 서비스에서 강한 기준선이다. **보편적 최강 기준선 대비 최종 승자는 UNKNOWN.**
- 병행이 순차보다 우월하다는 증거는 없다. 순차 승자를 그대로 인정한다.

## 최우선 후속 과제

현재 최신 감사: `research/SCOPE_DISTANCE_AUDIT_RESULTS.md`, `research/SCOPE_DISTANCE_NOVELTY_AUDIT.md`. 아래 OLD_P2 완료 체크포인트 이후 사용자 명시 지시로 전달 ZIP을 개봉·검증·독립 재빌드했다. 원본/추출본은 intake에 그대로 보존한다. 신규 기전은 맞지만 실제 파생 CPU 입력의 강한 서비스 우위 미확보, 기본 RCC 통합 없음, 후보 API plugin 미구현이다. 유일한 전체 gate 양성은 합성 oneway_dense/legacy/q32/ready이며 cold/unique에서 깨진다. 자동 추가 실험·GPU·병합 지시로 해석하지 않는다. 현재 API1.0.0 기존 세 모듈 실제 교체는 재검증 PASS다.

이전 OLD_P2 체크포인트 `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c`: 아래 미실행 계획은 `research/OLD_P2_SERVICE_RESULTS.md`와 `results/old_p2_service_20261021/`에서 완료했다. 고정3프로세스×7라운드, 반대 순서 sweep의 672 trials/14,112 전체 배열 PASS. original ready P2 대비 RCC/P2 q8=1.3045, q32=1.0667이므로 보편적 RCC 우위를 선언하지 않는다. 기존 원문 계획/자료는 역사적 맥락으로 보존하며 자동 재실행하지 않는다. 그 체크포인트에서 ZIP은 아직 미개봉·미실행이었다.

분리 시점의 미실행 계획: 새 알고리즘 전에 원본 OLD_P2와 동일 owned-output 계약의 cold/deferred/ready service 비교를 보완한다. LJ original+relabel, q8/q32, Push+EARLY_N/Push+RCC TABLE/OLD_P2를 고정 짝 비교한다. 세부 최소안은 보존된 SERVICE_BASELINE_GAP 문서에 있다. 기존 기록과 다른 측정 경계를 섞지 않는다. 최초 분리 작업에서는 그 성능 실험을 실행하지 않았다.

“이전 도달 범위로 다음 BFS의 검사 대상을 줄이기”는 `RESEARCH_CANDIDATES.md`의 DISCOVERY 후보다. 독립 효과·전체 비용·강한 baseline 비교 이전에는 기본 RCC에 합치지 않는다.

## MAIN 호환성

공통 API1.0.0, `prepare/can_apply/run/update/invalidate/release`. MAIN은 API만 포함한다. 실제 같은 MAIN 바이너리에 baseline/TABLE/LAST 동적 모듈을 교체하는 회귀검사가 있다. CPU 기능 호환성만 검증됐다. CUDA 백엔드는 UNSUPPORTED이며 미검증이다. CPU 성공으로 GPU를 통합 가능하다고 선언하지 않는다. 새 버전은 테스트 증거와 비용 측정 후 명시적으로 MAIN에 제안하며 자동 병합하지 않는다.

## 재개·안전·의존성

WSL 기존 g++15.2, Python3, C++20, pthread, dlopen. `python3 tools/verify.py`가 현재 worktree의 build/와 results/run_*에 기록한다. CUDA 정적 검사는 `tools/static_cuda.py`(기존 nvcc13.3와 mingw). 실행 바이너리·로그를 다른 worktree에서 덮어쓰지 않는다.

GPU 신규 작업에는 새 API backend와 구체적 dispatch 예산, source/binary/input pin, 최신 Windows PID/WDDM telemetry, start≥2048MiB/run≥1536MiB 여유, 온도<78°C, child20초/dispatch300초, 독립 watchdog, 에러 즉시중단·재시도0·warmup0을 요구한다. 과거 permit·PID allowlist를 재사용하지 않는다. 다른 작업을 종료하지 않는다. 유료 자원·paper 브랜치·외부 투고는 별도 승인 범위다.

Git: 매 의미 있는 검증 checkpoint마다 diff 확인→증거/한계 문서→commit→승인된 private remote push→remote SHA 대조. force push/이력 재작성/MAIN 자동 병합 금지. 마지막 SHA는 `git log -1` 및 `DELIVERY_STATUS.json`으로 확인한다. 세션 종료 후 자동 동기화는 없다.
