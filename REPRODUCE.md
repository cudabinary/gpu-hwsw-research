# 재현 및 복구

1. WSL에서 이 worktree로 이동한다.
2. `python3 tools/verify.py`: 기존 g++로 CPU API/세 shared module/MAIN client를 빌드하고 테스트한다. 매 실행 raw 로그는 새 `results/run_*`에 보존한다. 최초 n 필드 접근 컴파일 오류도 기존 results 루트에 남겼다. 수정 후 성공 결과와 구분한다.
3. `python3 tools/static_cuda.py`: 기존 nvcc13.3·mingw로 보존된 커널과 native owner 정적 빌드만 한다. GPU 실행 없음. 매 실행 별도 static_cuda_* 로그를 보존한다. 최초 host 컴파일의 CUDA include 경로 누락과 수정 후 결과를 구분한다.
4. `git worktree list`, `git status`, `git log -1`로 브랜치·현재 체크포인트를 확인한다. `git ls-remote origin refs/heads/main refs/heads/research/rcc`로 원격 SHA를 비교한다.

복구 가능한 로컬 보존본: 상위 `checkpoint/PRE_SPLIT_RESEARCH.zip`, 파일10,270개, 1,350,781,528 bytes. SHA256 `e043c998b3cf106c4edec2430617509ded8e7d785d71dbfe11debc6837d708bd`, ZIP CRC PASS. 전체 경로·크기·SHA는 같은 폴더 MANIFEST.json. 이는 대형 이전 trace까지 포함하므로 GitHub에는 올리지 않는다. Library 전송 helper만 제외했고 연구 source/raw/log는 포함했다.

기존 결과 ZIP은 `../../deliverables/TCSC_RCC_RIE_CONSUMER_CPU_GPU_PILOT_20261021.zip`, SHA256 `08a280c02d0cad82189e8ef1c925040df69ad4aabb2a33dd178c95efaee2631a`, Library `libfile_5c29472f6c10819182f6d87d202621ae`다. 원본은 그대로 보존한다.

Git bundle 제공 시 `git clone research.bundle restored`로 현재 버전 관리 코드·증거를 복원하고 `git worktree add ../rcc research/rcc`로 분리한다. 대형 로컬 checkpoint는 이 bundle에 포함되지 않는다. GitHub remote에는 소스·고정 입력·선별 원시 CPU/GPU 로그·회귀 결과를 보존하며 대형 trace·실행 바이너리·토큰·개인키는 제외한다.
