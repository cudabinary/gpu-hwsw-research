# DistanceGuard API 1.0.0 experimental validation — 2026-10-21

**The experimental CPU plugin passed API substitution and full-distance checks. Default RCC integration is on hold.** One synthetic ready condition retained an incremental benefit. On Google and LiveJournal, the plugin failed to establish a practical full-service advantage over both strong baselines and matched ablations. The campaign ended without further optimization rounds, MAIN changes, merges, or GPU execution.

## Pinned inputs and MAIN executable

The campaign ran in the `research/rcc` worktree. It checked 202 artifacts from independent audit commit `5c489f154d4c7c0bb587972ee307fcaf03a313e2` and 60 OLD_P2 artifacts from commit `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c` against Git blob bytes and SHA-256. The historical intake, results, and source also matched the files present at the time. Earlier reports, CSVs, ZIP, and vendor files stayed fixed. The input ZIP SHA-256 was `c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c` and all 92 manifest entries matched.

The existing `build/main_client` in the RCC and MAIN worktrees had the same SHA-256 before and after the campaign.

```text
d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e
```

Both copies of `libgraph.so` retained SHA-256 `11f75e3661fbd41a1e823d0f17f4c63e0007155d02eff6e02a23833873d5d795`. The baseline, TABLE, and LAST DSOs, shared API header, default `src/cpu_module.cpp`, and MAIN client source stayed pinned. The campaign ran the existing executable directly. Calling `tools/verify.py` would rebuild it. MAIN source, binaries, and API stayed fixed.

MAIN at `94a041c0bf300cd684ec1402244470dac499e55e`, its 219 tracked files and status, the 37 matching upstream files, and the 37 vendor files were checked before and after. Existing untracked `analysis/` and `evidence/audit/ORIGINAL_PRESERVATION_FINAL.json` on MAIN and earlier untracked RCC runs were preserved. See `results/dg_api_20261021/{PROTECTED,FROZEN,PREVIOUS}_{BEFORE,AFTER}.json`.

## Implementation and contract

The standalone code is in `research/dg_api_module.cpp`, `research/dg_api_kernel.hpp`, and `research/dg_api_factory.cpp`. It ports the supplied DistanceGuard loop and uses the frozen builder, consumer, and stop bridge. It implements API `0x00010000` with `rcc_create` and `rcc_destroy` for the CPU backend. The default factory and module selection do not load it automatically.

The module retains a completed API-owned immutable `Output` as the previous distance array. It allocates public output before traversal and certificate publication. After completion, it copies from workspace once and publishes the certificate by replacing shared ownership without allocation. It charges 4n bytes of retained distance data to the cache limit. Reader-owned output survives subsequent runs, invalidation, release, and destruction. The library stays mapped until process exit.

Certificates bind to the same Graph instance, identity, and version. Mismatch returns `INVALID_GRAPH`. Missing or disabled certificates, cache-limit failure, or injected cache failure use exact Push+EARLY_N. Finite row-budget requests also use the exact Push path, which supports row-boundary budgets. Pre-cancelled and partial runs publish neither output nor a certificate. Injected output allocation failure preserves the earlier certificate. Optional reverse-builder allocation failure triggers fallback. Failure to allocate required graph, workspace, or output memory returns `ALLOCATION_FAILED`. Cache and output failure injection and code inspection define the tested scope.

The plugin preserves the API's **`bound < n`** requirement. The original helper can use old distance labels when the prior reach count is n. The plugin uses and advertises certificates only for smaller bounds, which especially affects Google. External distance-array import, API expansion, and mutable borrowed output are outside the contract. Seeded prepare and update execute a full BFS and charge its cost.

Policy numbers are 0 Push, 1 TABLE, 2 LAST (matched controls), 3 OLD_P2, 4 Direction+RIE, 5 Direction+RIE+TABLE, 6 COUNT, 7 CLOSURE, 8 RADIUS, 9 FRONTIER, and 10 immediate exact-result reuse. `p9_0.so` is FRONTIER ready and `p9_1.so` is FRONTIER deferred. The `_phase.so` modules enable intrusive diagnostic timers. `dg_api_audit.hpp` and the optional `dg_audit_snapshot` symbol are diagnostic and outside the shared API. MAIN does not call that symbol.

The OLD_P2 and RIE performance wrappers run their original Direction algorithm before a certificate exists. They use the same owned-output and service boundary. Their fallback behavior is specific to the comparison. MAIN substitution covered the three deployed modules and four DistanceGuard variants.

## Actual module swaps and independent correctness

| Check | Result |
|---|---|
| Baseline BFS, RCC TABLE, and RCC LAST in the same existing MAIN | All three passed |
| DG COUNT, CLOSURE, RADIUS, and FRONTIER in ready and deferred modes | All eight passed |
| Each MAIN execution | 193,136 checks and 2,111 full arrays, including all 512 directed graphs on three vertices |
| Additional DG contract checks | 176 passed, covering graph instance and version, pre-cancellation, partial cancellation with row_budget=1, previous-certificate preservation after failure, finite-budget fallback, update, disabled mode, outputs surviving destruction, and full-reach fallback |
| Separate API diagnostics | 12 graphs × 2 source orders × 14 modes × 2 paths × 33 requests, yielding 22,176 matching arrays |
| Independent Python deque BFS from raw edges | 2,688 exported arrays and 6,544,608 elements matched across 12 graphs and 86 distinct graph-source oracle keys |
| Fixed primary service | 26,880 trials and 564,480 matching arrays, including rechecks after module destruction |
| Separate phase diagnostics | 1,008 trials and 33,264 matching arrays |

The existing MAIN checks for a zero cache limit, injected failures, output allocation failures, concurrent immutable readers, release, and reprepare passed for each substitution. Counts include repeated sources and graphs. Coverage applies to these CPU cases and the existing WSL Linux, g++, and C++ runtime ABI combination.

## Matched full-service measurement

The campaign pinned `DG_API_PROTOCOL.json` and all sources and binaries before timing. It used g++ 15.2 with C++20 and O2, **five sequential fresh processes, eight rounds, and two mirrored sweeps**, with zero warmups, performance retries, or post-result optimization. The matrix retained derived Google1024 and LJ4096 graphs, synthetic oneway_dense, legacy and distinct source lists, q8 and q32, ready and deferred preparation, and 14 modes. q counts follow-ups after the initial request.

All modes use the same exact Push+EARLY_N without a certificate for the initial request and the same subsequent source list. Immediate result reuse is limited to the separate EXACT_REUSE control. The earlier audit used shared exact-result reuse, a different first-request rule, and a borrowed-kernel boundary. Its timings remain separate.

`service_ns` adds the measured consumer output and container release interval to the continuous interval covering module construction, deferred preparation, API `can_apply` and `run`, algorithm execution, certificate maintenance, output allocation and copying, and `release` and destruction. Oracle validation falls between the two intervals and is reported separately. Ready shifts factory and preparation to measured historical work, which is added back in the history-inclusive metric. Deferred converts CSR and prepares workspace and cache inside the batch, building reverse at the first follow-up that needs it. Ready prepares them upfront.

Construction of the shared immutable API Graph, input I/O, the independent oracle, and one-time `dlopen` startup are outside the batch. The caller records `dlopen` separately on stderr and keeps libraries loaded. The tested service starts from the existing Graph. Deployed DSOs copy outputs twice. Matched TABLE/LAST and DG copy once. An incremental benefit must beat both the deployed modules and the matched controls. Primary timing disabled optional telemetry and detailed phase timers. Existing API counters and the new guard's logical counters remained active.

The analysis arithmetically averaged the two mirrored sweep times before taking the candidate/baseline ratio. Each condition had 40 paired blocks across five sessions. The rule required median below 0.95, at least 32/40 wins, and all five session medians below 0.95. A positive condition had to beat deployed and matched TABLE/LAST, OLD_P2, RIE, RIE+TABLE, EXACT_REUSE, DG_COUNT, and DG_RADIUS. The analysis retained descriptive 95% intervals from a fixed-seed 10,000-draw session-cluster bootstrap, session ranges, and all outliers. The five sessions occurred on one day. Multiple-comparison adjustment and across-day replication were outside the study. Across 336 same-policy mirror comparisons, median ratios ranged from 0.9147 to 1.0339 and the raw maximum was 6.0209.

## Full-service time and incremental benefit

The table gives median paired DG_FRONTIER / baseline ratios at ready q32. Parentheses give the descriptive session-cluster bootstrap 95% intervals. Ratios below 1 favor FRONTIER. See `PAIR_STATS.json` for all pairs, session medians, and win counts, and `COSTS.json` for absolute times.

| Graph and source order | / Deployed TABLE | / Matched TABLE | / OLD_P2 | / Direction+RIE | / DG_COUNT |
|---|---:|---:|---:|---:|---:|
| Google legacy | 0.9468 | 1.0021 (1.0005–1.0032) | 0.5994 | 0.5852 | 1.0004 |
| Google unique | 0.9015 | 0.9792 (0.9713–0.9843) | 0.6035 | 0.5947 | 1.0118 |
| LJ legacy | 0.9886 | 0.9840 (0.9755–0.9902) | 1.1013 | 1.1318 | 1.0519 |
| LJ unique | 1.0156 | 1.0058 (1.0055–1.0151) | 1.1256 | 1.1530 | 1.0560 |
| oneway legacy | 0.7896 | 0.7331 (0.7195–0.7672) | 0.0907 | 0.0863 | 0.1102 |
| oneway unique | 1.4125 | 1.3117 (1.3061–1.3213) | 0.3103 | 0.2939 | 0.7870 |

On Google legacy, the guard certificate applied to just two of 33 requests and performed **zero** distance-label reads. Each of the four DG ablations examined 131,150 edges. The extra filtering from the original helper did not carry over to this stricter API. The observed differences versus deployed TABLE include a single output copy and fallback changes. The legacy ratio versus matched LAST was about 1.02 and the full rule failed.

On legacy LiveJournal, FRONTIER reduced edge probes from COUNT's 874,228 to 825,955, a saving of **48,273**. RIE+TABLE used 815,173, so FRONTIER still performed 10,782 more probes than that control. API fallback and the common first request change the totals relative to the original helper. FRONTIER made 266,385 additional label reads. Including filtering costs, it was 5.19% slower than COUNT, 10.13% slower than OLD_P2, and 13.18% slower than RIE.

**The only condition meeting the full rule was synthetic `oneway_dense / legacy / q32 / ready`.** Ratios were 0.7896 against deployed TABLE, 0.8019 against deployed LAST, 0.7331 against matched TABLE, and 0.7301 against matched LAST, each with 37/40 wins. Matched TABLE session medians ranged from 0.7058 to 0.7903 and its bootstrap interval was 0.7195–0.7672. Ratios of 0.1102 against COUNT, 0.5808 against RADIUS, and 0.4267 against EXACT_REUSE also met the rule. Edge probes declined from 8,349,199 in COUNT to 2,057,647 in CLOSURE, 1,104,106 in RADIUS, and 406,837 in FRONTIER, isolating the filter effect. Slower outlier blocks were retained.

On the same synthetic condition, the ratio versus matched TABLE rose to about 1.30 deferred and about 1.31 when measured historical preparation was included. Ready distinct-source q32 was also slower, at 1.3117. No condition met the full rule with preparation charged. The remaining cases, including q8, failed at least one strong control. The limited ready result does not include an online selection cost or new real-world holdout.

## Preparation, maintenance, and adapter costs

The primary ready, legacy, q32 medians below are in microseconds. Historical preparation includes factory, CSR conversion, workspace and cache, and reverse construction where needed. Column medians may come from different trials.

| Graph and mode | Service | Historical preparation | Query total | Consumer release |
|---|---:|---:|---:|---:|
| Google matched TABLE | 222.47 | 23.36 | 220.50 | 1.40 |
| Google FRONTIER | 224.16 | 59.17 | 221.98 | 1.37 |
| LJ matched TABLE | 1652.77 | 156.17 | 1649.86 | 1.73 |
| LJ OLD_P2 | 1485.43 | 376.89 | 1482.63 | 1.78 |
| LJ FRONTIER | 1630.05 | 376.19 | 1626.50 | 1.72 |
| oneway matched TABLE | 527.14 | 429.49 | 524.37 | 1.45 |
| oneway FRONTIER | 387.07 | 872.91 | 384.53 | 1.34 |

The separate phase build enables detailed timers on the same algorithm core. The table gives median microseconds for six diagnostic trials at ready, legacy, q32. These measurements have their own instrumentation overhead and are separate from the primary ratios. The internal residual subtracts algorithm, allocation, copying, maintenance, and reverse phases from the same trial's run timer. It includes validation, branches, instrumentation, calls, and timer overhead.

| Graph | BFS and guard | Owned allocation | Output copy | Certificate maintenance | Internal residual | Prepare CSR | Prepare reverse |
|---|---:|---:|---:|---:|---:|---:|---:|
| Google | 223.721 | 7.116 | 1.775 | 0.846 | 4.257 | 22.088 | 53.538 |
| LJ | 1610.649 | 15.196 | 5.513 | 1.148 | 5.166 | 152.962 | 210.433 |
| oneway | 373.294 | 10.059 | 1.874 | 0.891 | 5.207 | 456.370 | 456.056 |

The deferred reverse phases were 36.590, 208.721, and 427.714 µs respectively, and are included in service. Ready still pays for an `ensure_reverse` check. Caller dispatch, the output vector, module release and destruction, and final consumer release are included in service and reported in the corresponding fields. The original non-diagnostic P2 path did not collect exact `inspected_edges` and sets `edge_available=false`. A zero placeholder means unavailable.

DG retained 4,096 bytes for Google and oneway and 16,384 bytes for LJ. Additional immutable CSR payload was 34,968, 532,500, and 225,944 bytes for Google, LJ, and oneway respectively. The totals omit some or all reverse, workspace, temporary edge pairs, allocator metadata, and retained outputs. Each primary and phase process reached 19,848 KiB peak RSS, including all loaded controls, fixtures, and oracles. The original helper swapped workspace arrays. The plugin updates its cache through shared ownership of an already returned API Output. Matched COUNT, TABLE, and LAST controls and measured copy cost account for the change.

## Decision, preserved evidence, and replay

- **CPU correctness and API.** The tested contract and actual same-MAIN swaps passed for the independent plugin.
- **Default integration.** HOLD. Default RCC and MAIN remained unchanged.
- **Conditional result.** The measured candidate gain applies to the ready module and reverse index, the fixed synthetic graph and its localized request sequence, and sufficient q. Distinct sources, preparation-inclusive paths, and real-world-derived inputs did not establish the same benefit.
- **Novelty and paper status.** The [prior audit](SCOPE_DISTANCE_NOVELTY_AUDIT.md) stands. The adapter and conditional timing provide implementation and performance evidence within this scope. Academic priority and a standalone paper contribution remain unestablished.
- **Campaign scope.** Zero further optimization rounds, new GPU runs, paid resources, or MAIN rebuilds followed the fixed campaign.

The output at `results/dg_api_20261021/` includes five raw service CSVs, phase CSVs, array JSONL, work CSVs, commands and logs, pins, uncertainty and cost JSON, and original preservation receipts. `RUNTIME_BINARIES.tar.gz` holds the executed binaries with size and SHA receipts. The compiler emitted two warnings on indentation and an enum conditional. The original logs retain them. There were no compile errors or failed trials and no post-result changes to source or run conditions.

For byte-exact replay or historical manifest checks, use the original checkpoint described in [the English edition provenance](../evidence/audit/ENGLISH_EDITION.md). The original commands are `python3 tools/run_dg_api.py prepare`, `python3 tools/run_dg_api.py benchmark`, and `python3 tools/analyze_dg_api.py`. They use a fresh copy and the existing pinned MAIN executable, libgraph, and default DSOs in the binary bundle. Prepare rejects an existing output directory, and benchmark is single-use. The historical integrity manifest and GitHub permission receipt are `ARTIFACT_SHA256.json` and `GITHUB_AUTH.json`. The local `DELIVERY_STATUS.json` recorded the original push, while the remote ref shows the current commit.
