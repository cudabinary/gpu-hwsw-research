# GPU HW–SW Research

MAIN은 강한 SW 기준선 이후 남는 GPU 구조적 병목을 연구한다. RCC 알고리즘 개발은 `research/rcc`에서만 진행한다.

최초 분리 체크포인트는 연구 환경 분리와 CPU 모듈 교체 계약을 확립했다. 새 알고리즘, 성능 개선, GPU 공통 API 호환성, 신규성 또는 HW 필요성을 입증하는 결과가 아니었다.

2026-10-21 RCC 후속 체크포인트: `research/OLD_P2_SERVICE_RESULTS.md`에 원본 OLD_P2의 동일 owned-output 서비스 비교를 보완했다. 원본 LJ에서는 reverse가 이미 준비된 P2에 대한 RCC의 우위가 성립하지 않으며 조건별 결론을 보존한다. 새 API 어댑터의 성능이나 새 알고리즘 기여로 해석하지 않는다.

- 공통 계약: `api/rcc/v1.hpp` (1.0.0)
- 원본 복사본: `vendor/rcc_20261021/` (SHA 고정)
- 이전 결과: `evidence/previous/`
- 역사적 GPU 검증: `evidence/audit/HISTORICAL_GPU_VERIFICATION.json`
- 새 CPU 호환성 결과: `results/COMPATIBILITY.json`
- 실행: WSL의 기존 g++/Python으로 `python3 tools/verify.py`

빌드·로그·출력은 각 worktree에 별도로 생성한다. 원본 연구 폴더는 읽기 전용으로 취급한다. GPU 실행에는 별도 backend 구현·검증과 현재 환경에 대한 안전 검사가 필요하며, 과거 실행 승인 파일을 재활성화하지 않는다.
