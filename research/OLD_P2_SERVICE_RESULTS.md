# Matched OLD_P2 service comparison with owned output — 2026-10-21

**The fixed CPU follow-up closed the original OLD_P2 baseline gap. The fastest path depends on the input and reverse-index availability.**

This experiment follows [the baseline-gap plan](../evidence/previous/SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md). It used the frozen executor, builder, P2, and A. Earlier data stayed separate. RCC, the shared API, and MAIN were unchanged, and the shared adapter's service performance was outside this comparison.

## Protocol and correctness

`OLD_P2_PROTOCOL.json` and the source, input, and binary hashes were fixed before timing. The original and existing relabeled LJ4096 fixtures used their original source lists at q8 and q32. q counts follow-up requests after the initial A request. Each trial used fresh workspace and cache state and returned independently owned immutable distance arrays. A used the frozen queue BFS. Service time included the count, certificate updates, and copies needed by RCC.

Exactly three performance workers ran sequentially with seven rounds each. Each round rotated and reversed four paths. Its second sweep used the exact reverse order. An independent C++ deque BFS matched every element across **672 trials, 14,112 arrays, and 57,802,752 elements**. Separate Python deque BFS matched **336 diagnostic arrays and 1,376,256 elements**. The totals include repeated graphs and requests. Retries, warmups, and new GPU runs were zero.

Geometrically averaging the two sweep ratios within each session, round, graph, and q produced 21 primary paired blocks per condition. The preregistered rule required a median below 0.95, at least 17/21 wins, and all three session medians below 0.95. This descriptive decision rule is separate from statistical inference.

## Service results

These are median paired `total_ns` ratios, RCC TABLE divided by each baseline. A ratio below 1 favors RCC TABLE.

| Fixture | q | / PUSH_N | / OLD_P2 deferred | / OLD_P2 ready |
|---|---:|---:|---:|---:|
| LJ original | 8 | 0.8808 | 0.7815 | 1.3045 |
| LJ original | 32 | 0.7948 | 0.9327 | 1.0667 |
| LJ relabel | 8 | 0.8700 | 0.5108 | 0.6824 |
| LJ relabel | 32 | 0.7979 | 0.5440 | 0.5845 |

RCC TABLE met the preregistered rule against PUSH_N and deferred OLD_P2 in all four conditions. On the original input, RCC took about 30.45% and 6.67% longer than ready OLD_P2 at q8 and q32. At q8, the reciprocal P2/RCC ratio of 0.7666 met the rule. At q32, **P2/RCC was 0.9375 with 20/21 wins**, but the session medians of 0.9519, 0.9208, and 0.9399 did not all meet the 0.95 threshold. P2 had the lower observed q32 time and its strict margin remained unconfirmed.

On the relabeled input, RCC also met the rule against ready P2. The inputs represent two vertex and row orderings of one graph. Source lists, thresholds, and paths stayed fixed after timing. The comparison covers four paths under these conditions, with historical Direction+RIE results reported separately.

## Costs and measurement boundaries

The primary `total_ns` retains the earlier service window. It includes workspace, executor, and cache allocation, frozen A, certificate and output copies, any deferred reverse build, and owned output delivery for q follow-ups. Input I/O, the oracle, output-vector reserve, validation, release, and scope teardown sit outside this interval. The same trials also recorded broader measures.

- `historical_prepare_ns` measures construction of a ready reverse index before service.
- `history_inclusive_ns` adds `total_ns` and `historical_prepare_ns` within each trial.
- `cleanup_window_ns` continuously measures service start through validation, output release, and destruction of workspace, executor, reverse index, and builder.
- `lifecycle_ns` continuously measures function entry through all cleanup and includes ready reverse construction and vector reserve. Initial CSR creation and input loading are outside its scope.

| LJ original | PUSH_N service (µs) | RCC TABLE service (µs) | P2 deferred service (µs) | P2 ready service (µs) | Ready reverse preparation (µs) |
|---|---:|---:|---:|---:|---:|
| q8 | 511.414 | 450.256 | 567.106 | 347.289 | 214.292 |
| q32 | 2069.968 | 1659.363 | 1772.812 | 1548.056 | 218.916 |

These are medians of raw times per path. The paired ratios use matched trials. `results/old_p2_service_20261021/COSTS.json` records A completion, preparation, validation, release, continuous lifecycle, and payload medians for every condition.

In `lifecycle_ns`, RCC/P2 ready was 0.7942 at original q8 and 0.9278 at original q32, meeting the numerical rule in both cases. This wider measure includes experimental oracle and identity checks. An application that already has a reverse index incurs no historical build cost on that request. Use the ready service interval for that workload and a preparation-inclusive measure when a new reverse index is required.

TABLE used 16,384 bytes at n=4,096. Initialization, counting discoveries in completed A, table scanning and writing, and later certificate updates are included in service. Maintenance was not timed independently. The conservative array payload bound, including the frozen builder's reverse and scratch arrays and all owned outputs, remained within 32 MiB. Worker peak RSS was 20,052 KiB. Extra CSR and output copies and `Trace=true` in the shared API adapter remain outside this performance result.

## Variability, preservation, and compatibility

Across 16 same-path sweep comparisons, median sweep 1 / sweep 0 ratios ranged from about 0.955 to 1.015. One original LJ q8 PUSH_N raw ratio reached 10.43. All outliers were retained and no run was repeated after looking at results. Pairing, mirrored order, and three short CPU sessions address within-campaign variation. Replication over independent dates and a statistical uncertainty estimate remain open.

`tools/audit_old_p2_service.py` passed a read-only check of the trial matrix, duplicates, gaps, mirrored order, timing boundaries, and source, binary, and protocol pins. Before and after checks covered 37 vendored files, their 37 upstream counterparts, and the MAIN worktree's 219 tracked files, HEAD, and status. Other files in the upstream workspace were outside that check. Existing untracked work was left in place.

The API remained at 1.0.0. A fresh `tools/verify.py` run loaded baseline, TABLE, and LAST into the same MAIN client, SHA-256 `d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e`. Each module passed 2,111 arrays plus existing tests for cancellation, graph identity and version, allocation failure, and owned reader lifetime. Those checks have a separate scope from the service comparisons. The CUDA API backend remained `NOT_IMPLEMENTED_NOT_VERIFIED`.

## Decision and reproduction

RCC showed value when the service would otherwise build a new reverse index. Ready P2 remained faster on the original input. The evidence applies to these CPU paths and leaves general performance leadership, adapter speed, GPU performance, novelty, and a standalone paper contribution open. Default RCC did not change.

The checkpoint contains source, raw CSVs and commands, correctness dumps, costs, variability, and preservation receipts. For byte-exact historical replay and pin verification, use the original checkpoint referenced in [the English edition provenance](../evidence/audit/ENGLISH_EDITION.md). The original WSL procedure uses a fresh copy with empty build and result directories.

```text
python3 tools/run_old_p2_service.py prepare
python3 tools/run_old_p2_service.py benchmark
python3 tools/run_old_p2_service.py analyze
python3 tools/audit_old_p2_service.py
```

The benchmark refuses a directory containing `BENCHMARK_STARTED.json`. Analyze and audit read historical raw data without starting performance workers.

The supplied RCC-Scope and DistanceGuard ZIP was still unopened and unused at this checkpoint. The planned independent follow-up covered integrity, correctness, matched service baselines, incremental value, and prior work before considering integration.
