# 호환성 증거 범위

| 항목 | CPU API1.0.0 | CUDA API1.0.0 |
|---|---|---|
| 비활성화/무인증 exact fallback | PASS | 미구현 |
| 활성 전체 배열·baseline 교체 | PASS | 미구현 |
| identity/version/instance 거부 | PASS | 미구현 |
| 변경 후 무효화·재준비 | PASS | 미구현 |
| pre-cancel/행 예산·비공개 부분 상태 | PASS | 미구현 |
| 캐시·출력 할당 실패 주입 | PASS | 미구현 |
| 반복 요청·release 후 독자 | PASS | 미구현 |
| TABLE/LAST 같은 인터페이스·알 수 없는 API 거부 | PASS | 미구현 |
| MAIN/RCC worktree 동일 client 결과 | 최종 CROSS_WORKTREE.json 참조 | 미검증 |
| 백엔드 지원 선언 | CPU true | CUDA false, UNSUPPORTED 반환 검사 |

동적 모듈은 동일 toolchain ABI를 가정한다. library unload는 지원하지 않으며 서로 다른 compiler ABI 호환성이나 미래 미작성 RCC v2/v3를 테스트했다고 하지 않는다.

역사적 CUDA owner의 36BFS+12취소 PASS 및 이번 복사본 정적 compile/link는 별도 증거다. 새 GPU 공통 API 호환성 검증에는 사용할 수 없다. 새 CUDA backend는 모든 해당 테스트 통과 전 통합 가능으로 선언하지 않는다.
