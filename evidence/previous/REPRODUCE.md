# 재현법

원본은 읽기 전용으로 보존한다. 새 복사본에서 실행한다.
필수 CPU 도구는 이미 설치된 WSL Python3, g++15.2(C++20), pthread다. 설치/네트워크는 필요 없다.

```text
python3 tools/cpu_driver.py build_test
python3 tools/cpu_driver.py benchmark
```

결과가 존재하는 배포 ZIP에서 재실행하려면 새 디렉터리에 코드·frozen·fixtures·config/PROTOCOL.json만 복사하고
빈 results/build/audit를 만든다. BENCHMARK_STARTED.json이 있는 폴더에서는 재시도를 거부한다.
benchmark는 정확히 3개 persistent CPU 프로세스를 시작한다. 각 프로세스가 GATE 후 기다리고,
사전 규칙으로 service_modes가 확정된 후 같은 프로세스에서 SERVICE를 진행한다.
원본과 다른 파라미터를 시험해 유리한 결과만 고르지 않는다.
CPU 원시 결과: results/gate_0..2.csv, results/service_0..2.csv, results/work.csv, distances.jsonl.
resident 결과는 총33요청, warm history는 과거3요청을 별도 기록한다.
service는 original q0/1/2/8/32이며 ready reverse 역사적 준비 비용을 따로 기록한다.

```text
/usr/local/cuda-13.3/bin/nvcc -std=c++17 -O2 -arch=sm_89 -Icuda --cubin cuda/kernels.cu -o build/rcc_kernels.cubin
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static -Icuda -Ifrozen/consumer -I/usr/local/cuda-13.3/include cuda/owner.cpp -o build/rcc_owner.exe
```

위 두 명령은 정적 컴파일이다. 실행 파일의 --abi / --cpu-check는 driver를 로드하지 않는다.
GPU launch는 raw exe 단독 호출로 진행하지 않는다. 최신 authorization, 새로운 정확한 PID baseline,
모든 pin, 유효 continuous guard, 새 단일 실행 디렉터리가 필요하다.
tools/gpu_pilot.py는 이미 결과 폴더가 있으면 재실행을 거부한다.
이 제출물의 과거 baseline/PID/token을 다른 날짜의 실행 권한으로 재사용하지 않는다.

GPU 결과/명령/원시 telemetry: results/GPU_PILOT. 드라이버 context 종료 확인도 보존했다.
정적 컴파일 출력: results/gpu_static_* / gpu_abi_*.
tools/report.py는 첨부 원본이 input/handoff에 있는 작업 폴더에서 감사/재집계를 한다.
배포 ZIP은 중복 첨부 archive를 제외했으므로 full report 재생성은 원본 첨부를 같은 위치에 읽기 전용으로 제공해야 한다.
핵심 CPU 재현에는 첨부 archive가 필요 없다.

최종 집계 감사는 `python tools/report.py` 다음 `python tools/strong_control_audit.py` 순서다. 후자는 기존 CSV만 읽으며 성능 실행을 하지 않는다.
