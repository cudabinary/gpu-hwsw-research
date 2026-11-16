# Reproducing the earlier consumer study

Keep the original snapshot read-only and run in a new copy. The historical CPU environment had WSL, Python 3, g++ 15.2 with C++20, and pthreads. Those installed tools were sufficient without network access.

```text
python3 tools/cpu_driver.py build_test
python3 tools/cpu_driver.py benchmark
```

To rerun from a distribution ZIP containing earlier results, copy the code, `frozen`, `fixtures`, and `config/PROTOCOL.json` into a clean directory and create empty `results`, `build`, and `audit` directories. The benchmark rejects a workspace containing `BENCHMARK_STARTED.json`. It starts exactly three persistent CPU workers. Each waits after GATE and then executes SERVICE within the same process once the predefined rules finalize `service_modes`. Keep the original parameters.

Raw CPU outputs are `results/gate_0..2.csv`, `results/service_0..2.csv`, `results/work.csv`, and `distances.jsonl`. The resident batch contains 33 requests, with the three historical requests that prime the warm certificate recorded separately. The service uses the original schedule at q0, q1, q2, q8, and q32 and records historical ready reverse-build cost separately.

```text
/usr/local/cuda-13.3/bin/nvcc -std=c++17 -O2 -arch=sm_89 -Icuda --cubin cuda/kernels.cu -o build/rcc_kernels.cubin
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static -Icuda -Ifrozen/consumer -I/usr/local/cuda-13.3/include cuda/owner.cpp -o build/rcc_owner.exe
```

These commands compile and link without launching GPU work. The executable's `--abi` and `--cpu-check` modes do not load the driver. An actual GPU launch used the pilot wrapper with current authorization, a fresh exact PID baseline, all relevant pins, continuous monitoring, and a new run directory. `tools/gpu_pilot.py` refuses to rerun in an existing results directory. Historical baselines, PIDs, and tokens apply only to the original pilot.

`results/GPU_PILOT` holds the original GPU results, commands, raw telemetry, and confirmation of driver context release. Static-build output is under `results/gpu_static_*` and `results/gpu_abi_*`. `tools/report.py` audits and aggregates in a workspace containing the original supplied files under `input/handoff`. The distribution ZIP omits duplicate input archives. Provide the original attachments read-only at that location for full report regeneration. Core CPU reproduction does not need them.

Run the final aggregation audit with `python tools/report.py` followed by `python tools/strong_control_audit.py`. The audit reads existing CSV results and runs no benchmarks.
