# RCC independent track

- 목표: 기본 RCC 및 전달받은 확장 후보의 정확성·전체 서비스 비용·강한 SW 대비 효과와 신규성을 독립 검증.
- 브랜치: `research/rcc`; 작업 경로는 이 파일을 포함한 repository root. MAIN은 별도 worktree다.
- 현재 성과: 원본 보존, CPU API1.0.0 동일 MAIN 바이너리 모듈 교체 재검증, 고정 OLD_P2 서비스 누락 보완 완료.
- 금지된 과장: GPU 성능 우위, 새 CUDA API 호환성, 신규 HW 필요성, RCC 신규성 모두 미확정.
- 다음: `research/OLD_P2_SERVICE_RESULTS.md`를 먼저 보고하고, RCC-Scope·DistanceGuard 전달 ZIP을 독립 감사. MAIN 수정·자동 병합 없음.
- build/log/output은 이 worktree 안에서만 생성.
- GitHub: 지정 private 저장소의 research/rcc만 허용 범위에서 Push. 실제 최신 SHA/Push 검증은 로컬 `DELIVERY_STATUS.json` 영수증과 `git ls-remote` 참조. 영수증은 자기 SHA 참조를 피하기 위해 commit 밖에 둔다.
