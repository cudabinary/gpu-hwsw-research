# Cost and interference in the CPU measurements

## Strongest-baseline audit

Original OLD_P2 is a valid non-RCC baseline. With the original LiveJournal input and a resident consumer, OLD_P2 took 0.7263 times as long as PUSH_N. The median paired DO_RIE / OLD_P2 ratio was **1.0505**. RIE reduced work relative to DO_N within the same adapter. Runtime also depends on exact discovery counting, termination checks, the bridge's validation and control logic, and code generation. The experiment did not isolate those individual contributions.

The initial service gate omitted OLD_P0 and OLD_P2. The configuration in `config/service_modes.txt` and the original aggregation were preserved. `CPU_INCREMENTAL_VALUE.csv` was regenerated from existing raw data to include these modes in the strongest resident baseline. The initial aggregation is retained in `results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv`. No additional CPU benchmark was run at this checkpoint.

In the measured cold q32 service, Push+RCC_TABLE took 0.7999 times as long as PUSH_N and 0.8999 times as long as sequential DO_RIE. **The strongest full-service path remains unknown at this checkpoint**, pending a comparison with original OLD_P2 under the same owned-output contract. The earlier P2 value of 0.840713 used a different measurement boundary. The minimum follow-up is a paired comparison of frozen P2's sequential and ready paths against Push+RCC_TABLE under the same output contract. It was outside this checkpoint's completed budget of three CPU processes with seven rounds each.

The GPU pilot checked correctness for two candidates and their controls. It passed cancellation, source switching, and full-array comparisons. Graph version mismatch, allocation failure, and dispatch limits were covered through CPU tests or static guards. The pilot did not inject those failures on the GPU or measure the missing CPU baseline.

Three independent workers ran sequentially, with seven rounds each. Total time was 25.66 seconds, with zero retries, threshold tuning runs, and warmups. Diagnostic counters and uninstrumented timing used separate template instantiations. Peak worker RSS was 22,844, 22,880, and 23,024 KiB. This includes all preloaded fixtures, reference results, and reverse indexes.

## Resident consumer on the original LiveJournal input, 33 requests

Ratios use PUSH_N as the baseline. q32 consists of one initial request and 32 follow-ups. The reverse index is resident. Cold certificate timing starts with executor initialization and certificate construction. Warm timing starts after three prior requests, whose cost is recorded as `priming_ns`. Graph, reverse index, and workspace setup are outside the resident window. The window includes copying new results, updating certificates, constructing caches, and destroying the executor. Validation and result release have separate fields, `validation_ns` and `release_ns`.

| Mode | Ratio | Wins | Edges saved |
|---|---|---|---|
| OLD_P0 | 1.0148 | 5/21 | -87282 |
| OLD_P2 | 0.7263 | 21/21 | 642244 |
| DO_N | 0.7922 | 20/21 | 642244 |
| DO_RIE | 0.7588 | 21/21 | 643391 |
| PUSH_RCC_TABLE | 0.7946 | 20/21 | 298187 |
| DO_RIE_RCC_TABLE | 0.7566 | 21/21 | 643391 |

The median paired DO_RIE_RCC_TABLE / DO_RIE ratio was 1.001252. RCC saved zero additional edge checks and zero vertex checks. Timing variation close to parity provides no evidence of an incremental benefit.

## Measured q32 service

A uses the frozen `plan_a`. A completion includes copying A's result and the count and scan used to build a certificate. A compute and completion have separate raw CSV fields. Total time includes the builder's count, scan, cursor, scatter, and verification, synchronization and joins, and workspace allocation. Ready paths record historical reverse-build time separately and include a sum with that history. That sum combines measured components. Input parsing and independent CPU validation are outside the compute window. CPU build time remains a CPU measurement.

| Mode | Path | Ratio | Including history | Wins |
|---|---|---|---|---|
| PUSH_N | csr | 1.0000 | 1.0000 | 0/21 |
| PUSH_WCC | csr | 1.0493 | 1.0493 | 2/21 |
| LAST_RESULT_REUSE | csr | 0.9977 | 0.9977 | 12/21 |
| DO_N | deferred | 0.9092 | 0.9092 | 21/21 |
| DO_N | concurrent | 0.9491 | 0.9491 | 17/21 |
| DO_N | ready | 0.7877 | 0.9133 | 21/21 |
| DO_RIE | deferred | 0.8941 | 0.8941 | 18/21 |
| DO_RIE | concurrent | 0.9343 | 0.9343 | 18/21 |
| DO_RIE | ready | 0.7716 | 0.8952 | 20/21 |
| PUSH_RCC_LAST | csr | 0.8151 | 0.8151 | 21/21 |
| PUSH_RCC_TABLE | csr | 0.7999 | 0.7999 | 20/21 |

Push+RCC performed well at cold q32 without a reverse index. With a prebuilt reverse index, compare against the ready Direction+RIE path. The measured sequential path beat concurrent preparation. The experiment did not implement an online policy with advance knowledge of q. `CPU_STRONG_SERVICE_COMPARISON.csv` pairs each result against the strongest observed non-RCC service path at the same q. This is a retrospective reporting baseline.

## Memory and excluded costs

Graph and reverse each use `8(n+1)+4m` bytes. Full builder peak is `24n+8+4m`. Push workspace uses `8n`, Direction `12n+8ceil(n/64)`, TABLE `4n`, and WCC `12n`. Owned results use `4n` per unique result. LAST retains ownership of a result. `LAST_RESULT_REUSE` aliases are counted once.

The conservative service payload bound assumes all results overlap the full builder peak. All cases fit within 32 MiB. Allocator headers, control blocks, and thread stacks are outside the formula and included in process RSS.

The service total ends when results are available. Caller release happens later, and final teardown of service owners and builders was not fully instrumented. Fine-grained differences and equivalence within 1% remain untested.

## Paired interference with A on the original LiveJournal input at q32

| Mode | Path | Metric | Median ratio / PUSH_N service |
|---|---|---|---|
| DO_RIE | deferred | a_compute_ns | 1.0473 |
| DO_RIE | deferred | a_completion_ns | 1.0535 |
| DO_RIE | concurrent | a_compute_ns | 1.0492 |
| DO_RIE | concurrent | a_completion_ns | 2.3947 |
| PUSH_RCC_TABLE | csr | a_compute_ns | 1.0086 |
| PUSH_RCC_TABLE | csr | a_completion_ns | 1.0386 |

A completion includes advance allocations, thread startup, and certificate publication. The experiment did not resolve small effects or interference of 1% or less.
