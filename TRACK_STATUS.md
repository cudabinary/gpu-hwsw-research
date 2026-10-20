# MAIN track

- 목표: 강한 GPU SW 뒤 남는 구조적 병목과 HW–SW 기회를 검증.
- 브랜치: `main`; 작업 경로는 이 파일을 포함한 repository root.
- 현재 성과: 원본 보존, MAIN/RCC 분리, CPU API1.0.0 모듈 교체 회귀검사.
- 금지된 과장: GPU 성능 우위, 새 CUDA API 호환성, 신규 HW 필요성, RCC 신규성 모두 미확정.
- 다음: `MAIN_NEXT_RESEARCH.md`; RCC의 OLD_P2 service 공정 비교 결과를 기다리되 자동 병합하지 않음.
- build/log/output은 이 worktree 안에서만 생성.
- GitHub: 지정 private 저장소로 동기화. 실제 최신 SHA/Push 검증은 최종 DELIVERY_STATUS 영수증과 `git ls-remote` 참조.
