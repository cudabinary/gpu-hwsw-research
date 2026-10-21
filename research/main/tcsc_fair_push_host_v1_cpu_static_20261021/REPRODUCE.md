# Reproduction and preservation

All GPU execution is unavailable/unapproved in this delivery. Do not invoke
`--execute` or set either old or new GPU permit environment variables.

The existing tools used for the single host compile are recorded in
`audit/COMPILE.json`. The compile command uses WSL Ubuntu's already installed
MinGW C++17 -O2 -static and CUDA13.3 headers; it does not compile a new kernel.
`tools/compile_host.py` refuses an existing new binary/receipt. Work in a fresh
copy with separate outputs for a rebuild; do not delete/overwrite preserved files.

Safe compiled CPU entries on Windows:

```text
build/owner_fair_v1.exe --fair-tests
build/owner_fair_v1.exe --abi
build/owner_fair_v1.exe --cpu-check fixtures/gpu_micro7.edges 7 7 3
build/owner_fair_v1.exe --cpu-check fixtures/gpu_micro7.edges 7 5 3
build/owner_fair_v1.exe --cpu-check fixtures/livejournal_sampled_4096.edges 4096 7 32
build/owner_fair_v1.exe --cpu-check fixtures/livejournal_sampled_4096.edges 4096 5 32
```

`tools/run_cpu_checks.py` performed these entries and captured fresh output arrays
using a CPU-only environment variable, with every TCSC GPU permit stripped.
It refuses an existing results directory. Independent Python BFS comparison is
part of that script, not a comparison only to the C++ replay.

The new wrapper supports only CPU mock/owned CPU protocol fixture backends:

```text
python wrapper/tests/run_mock_tests.py --output results/REPRO_MOCK_NEW
python wrapper/src/host_wrapper.py --cpu-child-fixture --output results/REPRO_CPU_CHILD_NEW
```

The CPU-child command starts the fixed non-GPU Python fixture and its independent
watchdog. It uses zero gaps for CPU protocol testing, not the prospective GPU
rest contract. `run_owned_child_tests.py` and `run_adapter_stop_tests.py` keep
exclusive fixed test directories; use a fresh extracted workspace/output layout
to reproduce without replacing saved raw records. No virtual/mock time or CPU
protocol payload is a GPU performance or distance-validation measurement.

The old owner/strict/ABI/kernel/cubin hashes were checked before and after in
`audit/ORIGINALS_BEFORE.json`, `audit/ORIGINALS_AFTER.json` and
`audit/STATIC_KERNEL_CONTRACT.json`. The owner diff is included. New source/
binary hashes and coverage are in `results/FINAL_SUMMARY.json`. CPU preparation
time/account data and static device projections are in
`results/PREPARATION_COSTS_CPU_AND_PROJECTIONS.csv`.

Private Git contains source/reports/sanitized small records and raw hash links.
Original binary, cubin, output arrays and unredacted logs are in the private
result ZIP. Published derivative bytes are distinguished by PUBLICATION_MAP.
SHA256SUMS covers delivery members; the external ZIP receipt records CRC and
whole-archive SHA-256. No B2 upload/backup certification or original deletion
is part of this task.
