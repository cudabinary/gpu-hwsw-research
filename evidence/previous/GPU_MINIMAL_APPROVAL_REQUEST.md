# 최소 GPU 계획 — 최신 사용자 승인으로 실행 완료

최초 요청의 CPU/static 제한 이후 사용자가 이 대화에서 GPU 사용을 명시적으로 승인했다.
승인을 다시 요구하지 않고 다음 한정 파일럿을 수행했다. 과거 F/P1/P2 승인 파일을 재활성화하지 않았다.
실행 manifest는 config/GPU_MINIMAL_PILOT.json이며 원본 소스·바이너리·입력·감시기 SHA pin을 보존한다.

- 질문: EARLY_N/RIE/RCC가 GPU level publication과 source 교대에서도 전체 거리 정확성을 보존하는가?
- 입력: micro7(중복·self-loop·단절·sink), LiveJournal4096, synthetic scc4_d32.
- 각 입력에서 PUSH_N / PUSH_RCC_TABLE / DO_N / DO_RIE, 총12개 프로세스.
- 프로세스마다 완료 BFS 3회(첫 인증 생성 포함)+명시적 취소1회. 총36 BFS+12취소=48 호출.
- 예산: 총300초, child20초, workspace32MiB, 시작 free≥2048MiB, 실행 free≥1536MiB, 관측 온도<78°C.
- warmup0, 자동재시도0, Nsight Systems/Compute0, sanitizer0. 추가 설치/외부 다운로드/유료 GPU0.
- 그래픽 컨텍스트 고정목록 밖 PID, 불명확/오래된 telemetry, CUDA 오류, 거리 mismatch, watchdog/VRAM/온도 위반 시 즉시 중단.
- 종료 후 context 종료가 확인되지 않으면 추가 GPU 실행 금지.

실측 14.91초, 12/12 PASS. 승인 부재로 남겨진 작업이 아니다.
다음 단계 후보는 same owner의 비계측 paired 소비자 측정과 GPU 전체 서비스 경계의 별도 설계다.
현재 pilot에는 중간 취소 검사·CPU reverse 구축·host validation이 있어 이를 전체 서비스 GPU 가속으로 해석하지 않는다.
이번 연구의 CPU 한정 반복 예산과 파일럿을 완료한 뒤 중단했으며 GPU 성능 캠페인을 무한 확장하지 않았다.
