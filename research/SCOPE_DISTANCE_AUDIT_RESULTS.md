# Independent audit of RCC-Scope and DistanceGuard — 2026-10-21

**Integrity, implementation, and tested CPU correctness passed.** The audit reproduced additional edge-probe savings. A strong full-service advantage on real-world-derived graphs and academic novelty remain unestablished. Default RCC integration is on hold.

## Source and provenance

The 2,528,431-byte input, `RCC_SCOPE_DISTANCE_CPU_20261021.zip`, had SHA-256 `c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c`. The audit preserved the original download and copied it byte for byte into the historical `intake/rcc_scope_distance_20261021/original.zip`. All 93 entries passed CRC, path, duplicate, and symbolic link checks. The manifest itself was the 93rd file. The other 92 matched exactly by size, hash, and coverage. These checks establish internal consistency and file identity. External signatures, author identity, and novelty were outside their scope.

The extracted package also passed the manifest. Four common sources (builder, consumer header and source, and stop bridge) and nine shared fixtures matched the pinned vendor files byte for byte. The audit rebuilt the verified C++ source with local g++ and kept outputs in this worktree. Supplied ELF binaries were outside the execution scope. The audit read the documents, two headers and probes, fixture and analysis tools, raw results, and retained error records. See `intake/rcc_scope_distance_20261021/INTAKE.json` and `results/scope_distance_audit_20261021/`.

## Independent correctness

| Check | Result |
|---|---|
| Scope rebuilt C++ test | 4,736 graph configurations and 416,768 mode-query comparisons passed |
| DistanceGuard rebuilt C++ test | 640 graph configurations and 51,200 mode-query comparisons passed |
| Rebuilt supplied probes on fixtures | Scope 8,712 requests and Guard 6,336 requests returned exact complete arrays |
| Shared owned-output harness | 12 graphs × 2 source orders × 16 modes × 33 requests gave 12,672 matching arrays. Retained results stayed valid after executor destruction. |
| Python deque BFS from raw edge lists | 1,824 supplied arrays and 4,440,984 elements matched, as did the same number from rebuilt supplied probes. The owned harness also matched 1,536 arrays and 3,739,776 elements. |
| Independent finite mathematical checks | 512 directed graphs on three vertices, 7,824 closure checks, 7,824 triangle checks, and 12,360 frontier-edge checks passed |
| Counterexamples | Reproduced failures from using a partial BFS prefix as closure, confusing incoming and outgoing mass, using frontier MIN, and treating temporary exclusion as permanently unreachable |

The counts include repeated requests, tiny graphs, and baseline runs. Python had 86 distinct graph-source oracle keys across 12 inputs. Reproducing provided arrays validates the computation on those inputs.

Across 14,256 diagnostic mode-query rows, `edges`, `vertex_tests`, and `levels` matched exactly between the original helpers and the shared harness. Reaggregation from raw timing rows matched Guard's 4,032 rows and 120 paired summaries and Scope's 13,464 rows and 792 timing summaries. Historical shared-container timing and new local measurements retain separate scopes.

Scope source and tests verified immutable closure publication, budget refusal, preservation of a valid certificate on injected publication failure or partial traversal, and rejection of mismatched graph or reverse identity. Guard tests verified a new exact run after interruption and a zero-cache path. The helpers take trusted internal domain and workspace inputs. The shared harness separately implemented complete owned outputs and allocation before certificate publication.

## Matched full-service contract

The study fixed `research/SCOPE_DISTANCE_PROTOCOL.json` before timing. Three sequential g++ 15.2, C++20, O2 workers ran seven rounds with two exactly mirrored sweeps and zero warmups or performance retries. The matrix included Google, LiveJournal, relabeled LiveJournal, synthetic scc4 and oneway_dense, legacy and distinct sources, q8 and q32, cold and ready reverse, and 16 policies. All **26,880 trials and 564,480 full arrays** matched. Total elapsed time was about 49.23 seconds and each worker's peak RSS was 20,444 KiB.

Every policy used the same resident immutable CSR, frozen reverse builder, workspace family, and immediate exact-result reuse for a repeated source. Certificate state was empty at the start. Each batch contained one initial request plus q follow-ups. Each returned array was immutable and owned. New arrays were allocated before certificate publication. Reusing an existing owned result preserved its lifetime.

`service_ns` includes output-vector reserve, cold reverse preparation, workspace and cache preparation, all queries and certificate updates, owned output copying, and executor, workspace, and reverse teardown. Input I/O, CSR parsing, historical ready preparation, oracle validation, and final consumer output release are outside the primary interval. Separate measurements capture preparation, queries and publication, historical reverse construction, validation, and final output release. The continuous `lifecycle_ns` includes ready preparation and experimental validation through final output release.

Each policy processes the common first source with its own algorithm. The earlier OLD_P2 comparison used a fixed external A and a different timing boundary. The shared harness matches contracts across its own controls. The extra CSR and output copying and `Trace=true` of the API adapter were outside this measurement.

The primary analysis geometrically averaged the mirrored ratios into 21 paired session-round blocks, from three sessions. The rule required a median candidate/baseline ratio below 0.95, at least 17/21 wins, and all three session medians below 0.95. Inputs and thresholds stayed fixed and all outliers were retained. The rule provides no multiple-comparison correction, confidence interval, or long-term replication. Across 640 same-policy mirror comparisons, median ratios ranged from 0.772 to 1.281 and the raw maximum was 7.60.

## Incremental work avoided

The following comparisons use the same initial request and 32 follow-ups, including a Direction+RIE control with existing RCC TABLE.

| Input and order | Direction+RIE+RCC TABLE edges | DIST_FRONTIER edges | Additional savings | Additional logical old-distance reads |
|---|---:|---:|---:|---:|
| Google legacy | 265,846 | 203,808 | 62,038 (23.34%) | 46,496 |
| Google unique | 156,882 | 148,361 | 8,521 (5.43%) | 19,881 |
| LJ legacy | 810,522 | 762,249 | 48,273 (5.96%) | 270,301 |
| LJ unique | 806,503 | 796,918 | 9,585 (1.19%) | 224,699 |

The matched DIST_COUNT, CLOSURE, RADIUS, and FRONTIER sequence retained the same previous array and update scheme. For legacy Google and LiveJournal, DIST_COUNT and FRONTIER had the same level and vertex-check counts. The additional savings therefore include candidate exclusion beyond early termination. The Google unique comparison against DO_RIE+TABLE does not assume identical level counts. See `MECHANISM_LEDGER.json` and `WORK_SUMMARY.json`.

Scope GLOBAL eliminated zero additional edge checks on legacy Google and LiveJournal. On LiveJournal it reduced vertex checks from 364,544 to 364,461. On synthetic scc4 legacy, COUNT to GLOBAL reduced edge checks from 3,296,735 to 249,311 and vertex checks from 135,168 to 39,936. Strong Push remained faster. WCC and compaction controls incurred their costs in the same service window.

## Time against strong baselines

These are median paired `service_ns` ratios for DIST_FRONTIER divided by each baseline at ready q32. A ratio below 1 favors DistanceGuard.

| Input and order | / RCC TABLE | / RCC LAST | / OLD_P2 | / Direction+RIE | / Direction+RIE+TABLE |
|---|---:|---:|---:|---:|---:|
| Google legacy | 2.2783 | 2.1150 | 1.0411 | 1.0833 | 1.0636 |
| Google unique | 2.1677 | 2.2453 | 1.0814 | 1.1148 | 1.0970 |
| LJ legacy | 0.9733 | 0.9580 | 1.0575 | 1.1276 | 1.1017 |
| LJ unique | 0.9901 | 0.9649 | 1.0900 | 1.1261 | 1.1116 |
| LJ relabel legacy | 1.7862 | 1.7498 | 1.0320 | 1.0977 | 1.1151 |
| LJ relabel unique | 1.6212 | 1.6163 | 1.0889 | 1.1352 | 1.1325 |

The small LiveJournal gains versus RCC alone missed the 5% and three-session rule. OLD_P2 and RIE remained faster. Scope GLOBAL, LOCAL, and COMPACT passed every fixed control in zero of 40 conditions.

The only condition passing the complete rule was **DIST_FRONTIER on synthetic `oneway_dense / legacy / q32 / ready`**. Its ratios were 0.8730 against RCC TABLE (12.70% lower time) and 0.8616 against LAST, each with 21/21 wins and at least 5% lower time in all three sessions. Its matched DIST_RADIUS ratio was 0.5960. It passed all eight preregistered controls (PUSH_N, RCC TABLE, RCC LAST, OLD_P2, RIE, RIE+TABLE, compaction, and WCC).

Against RCC TABLE the same condition took 2.0234 times as long when cold and 2.0278 times as long when adding measured ready preparation. With distinct sources at ready q32 the ratio was 3.9124. The positive result requires a prepared reverse index and the tested synthetic graph and localized requests. A low-cost online selection rule and a combination of the two extensions were outside this experiment.

The report also retains additional comparisons between FRONTIER and Scope GLOBAL, LOCAL, COMPACT, and DIST_COUNT from the same raw data. CSV rows marked `predeclared_pair=False` are exploratory.

## Preparation, maintenance, and memory

The following measured medians are for LiveJournal legacy at cold q32. Preparation includes actual reverse-builder time where needed. Each column has its own median.

| Policy | Prepare (µs) | Queries and publication (µs) | Service (µs) | Live cache payload |
|---|---:|---:|---:|---:|
| RCC TABLE | 1.389 | 1549.386 | 1551.531 | 16,384 B |
| OLD_P2 | 266.086 | 1400.278 | 1668.887 | 0 B |
| Direction+RIE | 267.964 | 1339.185 | 1612.912 | 0 B |
| Scope GLOBAL | 270.391 | 1524.161 | 1787.933 | 16,892 B |
| DIST_FRONTIER | 265.668 | 1507.337 | 1780.305 | 16,384 B |

Scope maintains a membership bitmap and vertex list, scans completed `distance[n]`, sums global indegrees, and can hold both old and new payloads during publication. COUNT pays the same cost. DistanceGuard retains a 4n-byte array and swaps buffers after completion. All modes still pay for owned returns and shared exact-result lifetime. On legacy LiveJournal, 270,301 additional old-distance reads correspond to 1,081,204 logical bytes at 4 bytes each. The 48,273 neighbor IDs avoided correspond to 193,092 logical bytes. These are logical payload counts. DRAM traffic, cache misses, and GPU instructions were outside measurement.

`COSTS.json` records preparation, queries including maintenance, validation, release, history, and lifecycle for all conditions. Maintenance was not separately timed. `payload_upper_bytes` accounts for graph, workspace, live cache, results, and builder scratch. It omits some transient old-plus-new Scope payload and allocator overhead, as recorded in `ANALYSIS.json`. Use measured peak RSS and array payload for their respective scopes.

## API, preservation, and integration

API 1.0.0, the default `src/cpu_module.cpp`, `api/`, `tests/main_client.cpp`, vendor, and MAIN remained unchanged in the historical audit. A fresh `tools/verify.py` rerun loaded baseline, TABLE, and LAST into the same MAIN client, SHA-256 `d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e`. Each passed 2,111 arrays.

The two supplied helpers lack `rcc_create`, `rcc_destroy`, and the `prepare`, `can_apply`, and `update` contract. Their borrowed outputs and level-budget cancellations have different semantics from the owned-output and row-budget API. Candidate compatibility was **NOT_IMPLEMENTED_NOT_VERIFIED** at this checkpoint. The shared owned harness aligned the research measurement boundary. Integration required a real adapter with tested fallback, allocation errors, graph identity and version, and output lifetime. The later [DistanceGuard API experiment](DG_API_RESULTS.md) evaluates that separate implementation.

Both extensions remained standalone candidates, with exactness, counterexamples, mechanism evidence, and the synthetic and real-input results retained. The [novelty audit](SCOPE_DISTANCE_NOVELTY_AUDIT.md) left a standalone contribution open. New GPU runs, paid work, sanitizer runs, and supplied binary executions totaled zero.

Before and after checks covered 37 vendor files, their 37 original counterparts, and 219 MAIN files, HEAD, and status. The audit revalidated 60 artifacts from OLD_P2 commit `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c` against their Git blobs and current historical source and results. Updated status documents and pre-existing untracked work had separate scopes.

During final preparation, Linux Git could not read a Windows-format worktree pointer. The fix read the existing MAIN object database directly and was pinned before timing. Passed correctness and API checks were reused. See `PREPARE_METADATA_REPAIR.json`. Performance retries were zero.

## Reproduction and evidence

For byte-exact replay and historical receipt verification, use the original checkpoint and ZIP described in [the English edition provenance](../evidence/audit/ENGLISH_EDITION.md). The original WSL procedure used a clean copy, Python, g++, and the original ZIP at the download path configured in the historical script. In the English checkout, the intake script accepts an explicit ZIP path for a fresh copy.

```text
python3 tools/intake_scope_distance.py
python3 tools/audit_scope_distance.py prepare
python3 tools/audit_scope_distance.py benchmark
python3 tools/analyze_scope_distance.py
```

The original scripts refuse to overwrite existing intake, build, or result directories and disallow performance retries. The retained raw CSVs, arrays, commands, stdout, stderr, pins, snapshots, statistics, and mechanism ledger can be inspected directly. The original artifact receipt is `results/scope_distance_audit_20261021/ARTIFACT_SHA256.json`. The local ignored `DELIVERY_STATUS.json` recorded the historical push. Use `git ls-remote` for the current remote SHA.
