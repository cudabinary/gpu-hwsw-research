# TCSC ready-consumer S2/S3 exploratory repeat

Two approved RTX 4060 Ti sessions completed on 2026-10-21. Twelve CUDA workers
returned 268 complete BFS distance arrays; C++ and independent Python each
checked those same 268 arrays. Four additional initialization-only cancellation
checks returned no distance output. No retry or additional session occurred.

Campaign start: 06:31:15.147506 UTC. Completion: 06:32:37.529835 UTC.
The 82.390-second campaign includes a 60-second no-dispatch gap and cleanup;
it is not GPU busy time. Sampled peak temperature was 42 C and minimum free
VRAM was 6839 MiB. All owned contexts synchronized, exited and were absent
from subsequent driver PID observations. No reported correctness/CUDA error,
OOM, watchdog or observed-environment stop occurred.

The contract is **ISOLATION_UNVERIFIED**. No protected process module/memory
inspection or OS, permission, driver or clock change was performed. The prior
strict guard and its HOLD evidence were preserved. Unknown external CUDA/WSL
activity cannot be ruled out by this experiment.

On the fixed LiveJournal-derived 4096-vertex input, all four new q32 paired
Direction5/lean-Push7 ratios were 0.5701 to 0.6024. This meets the prospective
0.95 exploratory margin. The earlier S1 ratios, 0.8758 and 1.0544, remain in
the report and calculations. No algorithm, binary, kernel or input change
explains the large Direction timing change between S1 and S2/S3; its cause
is UNKNOWN. No confidence interval, stable isolated advantage or general GPU
performance claim is made.

The measurement starts with resident CSR/reverse. CPU reverse construction,
native context/setup and H2D precede it. Query initialization, synchronization,
full D2H and owned-output publication are inside. This is not GPU builder,
preparation-inclusive service, sequential-versus-concurrent preparation, or
hardware-causality evidence. API 1.0.0 RCC CPU interchangeability is prior,
separate evidence; this legacy CUDA consumer does not validate a common API
GPU backend.

- `reports/RESULT.md`: all pairs, time/resource boundaries and limitations.
- `reports/NEXT_DECISION.md`: what the signal warrants and what it cannot show.
- `results/S2`, `results/S3`, `results/CAMPAIGN`: immutable execution records.
- `results/analysis_complete`: successful offline tables and summary.
- `results/analysis`: preserved partial output from one offline CSV-format error.
- `historical/S1`: historical receipt and timing logs, never counted as new runs.
- `config/PLAN.json`, `audit/PREEXECUTION_FREEZE.json`: frozen scope and pins.
- `src`, `include`, `build`, `fixtures`: unchanged source, executable, cubin and inputs.
- `REPRODUCE.md`: GPU-free verification and exact historical launch command.

This finite execution approval has been consumed. No further GPU dispatch is
authorized by these scripts or this report. No B2 backup was performed in
this round; Git publication and a Library delivery ZIP are not independent
raw-data backup/restore certification. No original was deleted or overwritten.
