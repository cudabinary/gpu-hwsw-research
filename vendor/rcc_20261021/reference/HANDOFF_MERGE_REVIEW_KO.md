# Consumer-first and RCC integration review — 2026-10-21

## Verification

The latest Codex ZIP (4,040,604 bytes) passed CRC and 197 internal hash checks. The RCC ZIP (2,125,643 bytes) passed CRC and 99 internal hash checks. All five shared `.edges` inputs were byte-identical across the two projects. This review used no new GPU runs, remote machines, profilers, installations, or external uploads.

The review recalculated statistics from 9,600 Codex consumer timing rows and 300 measured service rows. An independent rebuild passed 20,350 C++ assertions and 4,360 mode-source comparisons. A separate RCC source rebuild passed 348,672 BFS comparisons and 74,752 bound inequalities. The checks built the original sources and did not use supplied executables. Codex performance was recalculated from its records and was not rerun on the same PC.

## Consumer-first measurements

The consumer retained queue Push and Pure Pull and added fixed Direction P2 and stats-Push P3. On LJ4096, median paired P2/P0 was 0.612524 at q8 and 0.723170 at q32. At q8, edge checks fell from 386,329 to 160,393. Measured q32 CPU service ratios were 0.840713 for sequential preparation and 0.865155 for concurrent preparation, with 15/15 paired wins each. Reported median times were 2.066075 ms for CSR, 1.744309 ms sequential, and 1.782297 ms concurrent. Both improved total time in that condition, with sequential preparation faster.

Cold q1, q2, and q8 gains remained unestablished. At q8, sequential and concurrent ratios were 1.039705 and 1.103198. Ready warm results had separate historical preparation costs. At q32, concurrent A compute changed by +0.105% in the paired comparison. That measurement does not establish 1% noninferiority. A completion roughly doubled with preparation and thread startup. Zero of 75 concurrent runs conservatively confirmed publication before A finished.

The supplied inputs, baselines, and timing boundaries support `CPU_CONSUMER_BENEFIT_CONFIRMED`, conditional `END_TO_END_GAIN_CONFIRMED`, and `CONTINUE_SW`. The older zero-success TCSC decision remains a record of its version. GPU gains, superiority of concurrent preparation, and algorithmic or hardware novelty remain open.

## Differences between the original consumers

RCC's Direction reference estimates remaining work from outgoing edges and tests membership using `distance == level`. Codex P2 maintains the exact sum of undiscovered indegrees and uses bitmap membership. The implementations' absolute times and ratios have different scopes.

Codex P0 does not stop when n vertices are found, and P2 lacks exact early termination. RCC includes EARLY_N as a required control. The original RCC_TABLE uses an accumulating queue. Codex P2 overwrites a frontier queue, so connecting it directly would mishandle either the visited set or the cost. A shared adapter can vary the traversal algorithm and stopping certificate independently.

## Independently implemented RIE termination

Codex P2 already maintains `remaining = sum(indegree(v) for v not yet discovered)` for direction selection. At zero, no edge enters an undiscovered vertex. The source is already discovered, so no undiscovered vertex can be reachable. The exact complete BFS distance array can be returned at that level boundary. The condition can trigger below the bound n and requires no future requests.

This sufficient condition follows directly from graph theory. The implementation reuses a direction-selection counter as a stopping certificate. Academic priority remains unestablished. A GPU implementation must account for exact reductions or atomics and level publication.

The probe used the same Codex policy and added N-stop, RIE, RCC_LAST/TABLE, RIE+RCC, and maintenance-matched OFF controls. It passed 87,552 new C++ comparisons, 550,224 inequalities, and 7,128 fixture requests. Python BFS over raw edges matched all 864 exported complete arrays (2,313,312 elements). GPU and sanitizer runs totaled zero.

## Combined paths

The original LiveJournal 33-request schedule produced these counts.

| Consumer path | Edge checks | Levels | Vertex-state checks |
|---|---:|---:|---:|
| Same Codex Direction, no added stop | 815,788 | 205 | 479,232 |
| Direction+n stop | 815,788 | 203 | 471,040 |
| Direction+RIE | 814,641 | 173 | 368,640 |
| Direction+RCC_TABLE | 814,641 | 174 | 372,736 |
| Direction+RIE+RCC_TABLE | 814,641 | 173 | 368,640 |

Across two existing LiveJournal source orders and the vertex-relabeled fixture, RCC saved zero additional edges or levels after RIE. TABLE still paid its memory and maintenance costs.

On disconnected synthetic SCCs, edges among globally undiscovered vertices can keep RIE above zero, so RCC can supply additional information. On scc4_d32 with the original order, Direction+RIE used 6,542,466 edge checks and RIE+RCC used 3,396,738. Push+RCC used 284,064 in the same condition and provides a stronger comparison.

The review preserved 10,584 resident CPU timing rows across three processes and seven rounds. Some synthetic cases showed large combined gains. Incremental gains on small real-world-derived inputs remained unestablished. The independent environment was AMD EPYC 9V74, g++ 14.2.0, and O3. The Codex measurements used i5-14500, g++ 15.2.0, and O2. The reported 2.066 ms and the new absolute times were measured separately. `original` and `holdout` denote previously inspected schedules from the RCC package.

## Follow-up

1. Retain the validated Codex builder and Direction implementation. Keep the concurrent builder outside the immediate research focus.
2. Include Push+EARLY_N and Direction+N/RIE when measuring RCC's incremental value on the same backend.
3. Report warm resident consumption and actual cold service costs for Push+RCC and Direction, including certificate maintenance, WCC preparation, and repeated-source result reuse.
4. Enable the combination only where it wins. Give synthetic gains their tested scope.
5. Complete the CPU adapter with complete distances, version checks, and safe lifetimes. Prepare a functional CUDA harness statically and propose a small, separately authorized GPU pilot.

## Research roles

- Codex handled same-backend integration on the original PC, factorial comparisons of consumer and certificate, cold and warm service, and static CUDA harness preparation.
- The ChatGPT track handled sufficient conditions, counterexamples, and minimal state. It implemented and validated RIE and the bridge. Whether previous closure can shrink the set of vertices or edges examined remains a follow-up hypothesis.
- Each track preserved the other's original data, ongoing work, and GPU resources. This handoff scheduled no future background work.

## Evidence

Codex sources include `FINAL_DECISION.md`, `CONSUMER_VALUE_REPORT_KO.md`, `COST_AND_INTERFERENCE_ANALYSIS.md`, `src/consumers.cpp`, `src/bench.cpp`, `frozen/independent_builder.hpp`, `results/CONSUMER_RAW_TIMINGS_LONG.csv`, and `results/PREPARATION_PLUS_CONSUMER_RESULTS.csv`.

RCC sources include `include/rcc.hpp`, `include/baselines.hpp`, `docs/DESIGN_AND_PROOF_KO.md`, and `RESULTS_KO.md`. The independent bridge records include `independent_bridge/results/BRIDGE_WORK_SUMMARY.csv`, `BRIDGE_PAIRED_SUMMARY.csv`, `test.json`, and `PYTHON_ARRAY_CHECK.json`.

Beamer et al. describe direction-optimizing BFS. The GAP Benchmark Suite is a separate high-performance reference and was outside the probe's build and runtime scope. This limited comparison leaves academic priority for RCC and RIE open. [Direction-Optimizing Breadth-First Search, SC 2012](https://www.scottbeamer.net/pubs/beamer-sc2012.pdf) · [GAP Benchmark Suite](https://github.com/sbeamer/gapbs)
