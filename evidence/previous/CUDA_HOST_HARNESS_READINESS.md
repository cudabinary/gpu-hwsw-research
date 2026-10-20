# CUDA owner / harness 및 실행 상태

`cuda/owner.cpp`는 실제 입력 로드·frozen CPU reverse 구축·GPU 할당/전송·BFS level driver·정답 비교·cleanup을 포함한다.
빈 main이나 링크 전용 stub이 아니다. Windows native Driver API header는 기존 검증된 복사본을 사용했다.
PTX/cubin sm_89, native Windows cross link, Linux/Windows ABI 비교 PASS.
GPU View=112바이트, Counter=24바이트다.

실행 모드: 0 PUSH_N, 1 PUSH_RCC_TABLE, 2 DO_N, 3 DO_RIE.
유망 후보 2개와 해당 강한 대조군이다. RIE가 RCC를 흡수한 Direction+RCC는 GPU에 넣지 않았다.
CPU의 reverse builder를 사용한 **resident consumer 정확성 파일럿**이다. GPU reverse builder나 GPU 병행 Plan A 전체 서비스는 실행하지 않았다.
GPU의 Push 종료는 레벨 경계라 CPU 행 경계 성능을 그대로 예측할 수 없다.

GPU oracle은 host deque BFS 전체 배열이며 history reader도 재확인한다.
출력 복사와 host TABLE publication 시간을 별도 기록한다.
stream_interval_ms는 host 제출/동기화 간격을 포함한 CUDA event 간격이며 순수 kernel busy time이 아니다.
원시 pilot wall_ms는 1회 측정이고 cold module/OS 간섭을 포함하므로 성능 최종 판정에 쓰지 않는다.

정확한 신규 발견 counter / remaining indegree 감소를 stream 완료 후 읽는다.
불완전/취소 결과는 TABLE을 갱신하지 않으며 다음 source로 재실행한다.
graph는 owner 수명 동안 immutable; numeric version만으로 외부 reverse를 받아들이지 않는다.
device count≤n, source/edge 범위, 32MiB 할당, epoch wrap, 128레벨/2040 dispatch 경계를 검사한다.
CUDA 오류 후 owner는 실패 상태이며 추가 query를 거부한다.

실제 결과: 36 BFS + 12 cancellation PASS, 12 processes, 232 kernel launches.
전체 14.907초; 최대 자체 device payload 1,163,820바이트.
telemetry 40개; 최소 free 6878MiB, 최대 44°C.
각 child의 explicit synchronize/context-release marker와 SMI PID 소멸을 확인했다.
Native module/engine monitors, 신선도 3초, 20초 child watchdog, 총300초 dispatch 제한을 유지했다.
watchdog는 이미 실행 중인 단일 GPU kernel을 즉시 선점하는 보장이 아니다. bounded input/loop/launch가 그 위험을 줄인다.
