# Independent study — extending RCC from termination to candidate exclusion

This standalone CPU study ran on October 21, 2026 without access to the other Codex worktree, the original home PC, or a GPU.

**The prototypes removed edge probes beyond RIE+RCC stopping. A stable CPU time advantage against strong baselines on real-world-derived inputs remains unestablished.**

`closure_scope.hpp` narrows the spatial search scope. `distance_guard.hpp` uses previous distances to defer candidates that cannot enter the next frontier. Both return exact complete distance arrays. GPU performance and academic priority remain open.

## Spatial scope

When a completed reachable set `R = Reach(r)` contains the new source, Pull skips destinations outside R. This reduces candidates while traversing. The study compared COUNT_ONLY with the same maintenance cost, global policy, scope-local policy, and compact unvisited-list variants.

The fixed matrix included 12 inputs, two source orders, and q8 and q32. Nine inputs came from the earlier bridge and three were synthetic counterexamples or positive cases. `legacy` was previously known. `unique` used 33 distinct sources fixed before timing. All methods reused the result for an immediately repeated source.

On synthetic scc4, legacy q32, COUNT_ONLY to SCOPE_GLOBAL reduced edge checks from 3,296,735 to 249,311, with median paired speedup 4.774×. Push+RCC_TABLE was still faster. Scope narrowing also worked on a synthetic one-way-connected graph but lost to stronger Push.

On legacy LiveJournal, the reachable region was nearly the entire graph and scope saved no edge checks. Legacy Google also saved none from spatial restriction. Small timing fluctuations provide no evidence of skipped work.

Separate controls used an unvisited-list compaction and WCC scope, with WCC construction charged to each batch. On disconnected graphs, WCC can provide the same scope. The correctness-tested CPU references were evaluated independently of GAP and cuGraph library performance.

## Distance-based candidate exclusion

Retain the previous completed distance array and swap buffers after completion. This requires no new edge scan or reverse build. The retained array costs 4n bytes. The separate full output copy is included in timing.

- LAST_COUNT uses only cardinality stopping.
- LAST_CLOSURE skips destinations outside the prior reachable set.
- LAST_RADIUS skips current candidates with `d_old(v) > d_old(s) + level + 1`.
- LAST_FRONTIER skips current candidates with `d_old(v) > 1 + max(d_old(frontier))`.

All variants use the same Direction, exact RIE, and cardinality stopping path. Candidates can return at later levels. The current distances remain exact and independently computed.

### Added savings on real-world-derived inputs

These are matched source lists with an initial request and 32 follow-ups. Every method used immediate repeated-result reuse. Earlier bridge checks used a different measurement contract.

| Input and order | Direction+RIE edge checks | LAST_FRONTIER | Reduction |
|---|---:|---:|---:|
| Google legacy | 265,846 | 203,808 | 23.336% |
| Google unique | 157,045 | 148,361 | 5.530% |
| LiveJournal legacy | 810,522 | 762,249 | 5.956% |
| LiveJournal unique | 806,503 | 796,918 | 1.188% |

Cardinality RCC alone saved zero additional edge checks for both LiveJournal orders. Prior distance values therefore support actual candidate exclusion beyond RCC counts and RIE. These counts measure logical edge probes. GPU instructions, DRAM bytes, and execution time require separate measurement.

## CPU cost of the guard

The legacy q32 logical read ledger records two different operations.

| Input | Neighbor IDs avoided | Additional old-distance reads |
|---|---:|---:|
| Google | 62,038 | 46,496 |
| LiveJournal | 48,273 | 270,301 |
| oneway_dense (synthetic) | 10,039,546 | 86,799 |

Each element is 4 bytes. On LiveJournal, old-distance reads account for about 1.081 MB of logical payload and avoided neighbor IDs about 0.193 MB. Caching changes physical DRAM traffic. Full distance initialization, result copying, and frontier bitmaps still incur costs.

Three processes with seven rounds measured batches with resident reverse and cold certificates. Relative to DO_RIE, LiveJournal LAST_FRONTIER had median paired speedups of 0.855× for legacy and 0.886× for distinct sources. All three session medians favored DO_RIE. Google unique showed a small improvement relative to DO_RIE, with stronger Push much faster.

## Conditional positive result

Synthetic `oneway_dense` has directed links between dense regions in one WCC. At legacy q32, LAST_FRONTIER showed a 1.639× median paired speedup versus Push+RCC_TABLE, won 19 of 21 pairs, and improved all three process medians. The 13.585× speedup versus DO_RIE uses a much slower baseline for this input.

With distinct sources on the same graph, the speedup versus Push+RCC_TABLE fell to 0.346×. The effect depends on the synthetic graph and request locality. FullBitset, GAP, cuGraph, GPU, and other indexing techniques remain outside the comparison. Reverse was already resident. The second-stage guard has no cold reverse end-to-end measurements.

## Executed verification

| Check | Scope | DistanceGuard |
|---|---:|---:|
| C++ mode-query comparisons | 416,768 | 51,200 |
| Test graph configurations | 4,736 | 640 |
| Preserved fixture requests checked | 8,712 | 6,336 |
| Independent Python full arrays | 1,056 | 768 |
| Uninstrumented timing rows | 13,464 | 4,032 |

The two suites share some tiny graphs and baselines. Python deque BFS over the raw edge files matched 1,824 arrays and 4,440,984 elements. The second Python suite also checked 7,824 triangle inequalities and 12,360 frontier-edge bounds on all 512 directed graphs with three vertices.

GPU, remote-machine, Nsight, sanitizer, external upload, and installation counts were zero. This was a single-owner CPU reference study.

## Timing and memory limits

The host used Intel Xeon Platinum 8573C with g++ 14.2.0 and O3. Earlier EPYC and i5 measurements have distinct machine and compiler conditions. Shared-container timings varied widely and all outliers were retained. Three processes on one host provide within-campaign variation.

Scope tested both resident and separately timed cold reverse. DistanceGuard tested resident reverse only. GPU interference, cause, and power remain unmeasured. Workspace, retained result, and cache figures are array payloads. Peak process memory requires a separate measure. Push `levels=0` records an uncollected counter.

## Later integration

The study did not modify ongoing Codex work or send messages to it. Keep the prototypes as independent candidates for same-backend review.

1. Compare guard work counts against the existing Direction+RIE.
2. Leave the guard disabled by default on real inputs given the observed CPU cost.
3. Use matched ON/OFF controls to isolate RIE and cardinality stopping, spatial scope pruning, and temporary distance filtering.
4. GPU evaluation would need exact previous distance storage, frontier max reduction, publication, and result-lifetime costs under a separate run plan.
5. Measure whether saved memory requests offset extra checks before making a hardware case.

**Status.** `EXACT_CANDIDATE_PRUNING_IMPLEMENTED / REAL_DERIVED_WORK_REDUCTION / CPU_BENEFIT_CONDITIONAL_SYNTHETIC_ONLY / GPU_UNMEASURED / NOVELTY_NOT_ESTABLISHED`.
