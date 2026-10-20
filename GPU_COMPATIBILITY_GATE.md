# CUDA 호환성 gate: 미완료

공통 API1.0.0의 `Capabilities.cuda=false`; `prepare(backend=CUDA)`는 UNSUPPORTED_BACKEND를 반환한다. 이 거부 동작은 CPU 계약 테스트에서 확인한다. **실제 CUDA 공통 API 호환성 PASS가 아니다.**

보존된 기존 owner/커널의 GPU 파일럿36 BFS+12취소 PASS는 코드·바이너리 SHA 및 stdout과 대조했다. 원본 CUDA를 복사본에서 정적 컴파일하는 것 역시 새 API 통합 테스트를 대체하지 않는다.

남은 구현: native owner에서 공통 API lifecycle로 연결하는 어댑터, 완전한 owned-distance 반환, Graph identity/version 검사, 취소·OOM·실패 후 재사용 정책, 라이브러리/driver 수명, exact baseline fallback, 계측 비용 경계.

다음 실제 검증은 구현 후 소스·바이너리·입력 pin을 고정해야 실행 가능한 계획이 된다. 제안 상한은 기존 pilot와 같은 12프로세스/36 BFS/12취소, 3입력(micro7,LJ4096,scc4_d32)×4검증 경로, child20초·전체300초·workspace32MiB, startfree2048MiB/runfree1536MiB·78°C미만, warmup/retry0이다. 각 경로는 baseline/RCC 교체·동일 배열·취소 후 비공개 상태·재실행을 검사한다. 실제 API backend가 미구현이므로 현재 새 SHA와 정확한 kernel 수는 미정이다. **이 문서는 지금 실행할 승인 플래그가 아니다.**

fresh PID/WDDM·VRAM·온도·독립 watchdog·종료 후 CUDA 작업 종료 확인이 모두 필요하다. 다른 계산 작업·불확실한 telemetry·오류·정확성 실패·watchdog·메모리/온도 위반에서는 추가 dispatch를 중단한다. Nsight/유료 자원은 이 계획에 포함하지 않는다.
