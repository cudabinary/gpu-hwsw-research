# Fixed-owner host wrapper: CPU mock implementation

The new host coordinator and append-only ledger are implemented in separate
files. **The live GPU adapter is unbound and unconditionally disabled.** The
only executable backend is a CPU mock with a virtual clock. No CUDA, process
launcher, device query or old GPU runner is imported by the coordinator.
Changing a permission flag cannot enable GPU dispatch in this version.

Current result: **24 CPU mock contract tests PASS**, with zero actual GPU
queries/dispatches, BFS correctness/performance runs, compilations or installs.
Every time, memory value, array-check flag and retirement flag in the mock
receipts is synthetic. They are not CPU timing, GPU accuracy or GPU safety
measurements. Real OS memory counters/watchdog/monitor coverage remain untested.

- `src/host_wrapper.py`: 217-line coordinator, event boundaries, numeric budget
  checks, sticky stop state, exclusive output paths and default-disabled dispatch.
- `src/mock_backend.py`: virtual clock and deterministic failure injections.
- `tests/run_mock_tests.py`: fixed order, gates, error/cancel/interrupt, budget,
  unknown-memory, retirement, stop/no-followup and raw-preservation checks.
- `config/PLAN_CPU_ONLY.json`: fixed [7,5,5,7] target order, same application
  caps and safety declarations; execution_authorized remains false.
- `COST_ACCOUNTING_AND_BASELINE.md`: separate safety/test and preparation costs;
  no reverse-free Push path exists inside the unchanged owner contract.
- `GPU_INTEGRATION_DELTA.md`: exact unimplemented live integration boundaries
  and the additional approvals needed before any GPU dispatch.
- `results/CPU_MOCK_TESTS_V2/TEST_RESULTS.json`: final 24-case result.

The first 23-case suite passed. A code review then added KeyboardInterrupt
cleanup/stop handling and its negative test. The complete 24-case suite passed
in a new V2 folder; the original 23-case raw records were retained. This was
a small CPU implementation revision, not a retry of any GPU experiment.

Original owner/binary/cubin/runner hashes are preserved in
`ORIGINAL_SOURCE_PINS_BEFORE.json` and `ORIGINAL_SOURCE_PINS_AFTER.json`.
No old result, strict guard, RCC file or original ZIP was modified. The new
coordinator is slightly larger than the prior 120-200 line estimate (217 lines);
no broad refactor or live adapter implementation was attempted. Mock and test
code are additional scaffolding. The original monolithic GPU guard was not
split or weakened to fit this estimate.

ISOLATION_UNVERIFIED remains the prospective contract. This work establishes
neither a fair strongest-baseline cold-service advantage nor hardware need,
and does not change MAIN's research direction.
