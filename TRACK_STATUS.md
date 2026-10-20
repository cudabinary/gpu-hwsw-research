# RCC independent track

최신 체크포인트: `research/DG_API_RESULTS.md`. DistanceGuard API1.0.0 실험 plugin 구현 및 **기존 MAIN 무재빌드 교체 PASS**. Google/LJ의 강한 고유 전체시간 우위는 미확보, 합성 oneway_dense/legacy/q32/ready만 조건 양성이고 준비 포함 시 역전된다. **기본 통합 HOLD**, 추가 최적화 반복0·새 GPU0·유료 자원0. 이전 감사·OLD_P2 증거는 불변 보존했다. 아래 후보 API 미검증 상태는 이전 체크포인트의 기록이다.

- 목표: 기본 RCC 및 전달받은 확장 후보의 정확성·전체 서비스 비용·강한 SW 대비 효과와 신규성을 독립 검증.
- 브랜치: `research/rcc`; 작업 경로는 이 파일을 포함한 repository root. MAIN은 별도 worktree다.
- 현재 성과: 원본 보존, 기존 CPU API1.0.0 동일 MAIN 바이너리 교체 재검증, OLD_P2 서비스 보완, RCC-Scope/DistanceGuard 무결성·재빌드·정확성·전체 서비스 독립 감사 완료.
- 금지된 과장: GPU 성능 우위, 새 CUDA API 호환성, 신규 HW 필요성, RCC 신규성 모두 미확정.
- 판정/다음: `research/SCOPE_DISTANCE_AUDIT_RESULTS.md` 참조. 실제 파생 입력의 강한 서비스 우위·최초성·후보 API 호환성 미확립. 기본 RCC 통합 없음, 독립 후보로 보존. MAIN 수정·자동 병합 없음.
- build/log/output은 이 worktree 안에서만 생성.
- GitHub: 지정 private 저장소의 research/rcc만 허용 범위에서 Push. 실제 최신 SHA/Push 검증은 로컬 `DELIVERY_STATUS.json` 영수증과 `git ls-remote` 참조. 영수증은 자기 SHA 참조를 피하기 위해 commit 밖에 둔다.
