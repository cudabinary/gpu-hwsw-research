# RCC research handoff

## Latest checkpoint — DistanceGuard API 1.0.0

Start with [DG_API_RESULTS.md](research/DG_API_RESULTS.md). The experimental plugin is separate from default RCC. Tests loaded all three existing modules and four DistanceGuard variants in ready and deferred configurations into the unchanged MAIN executable. The primary campaign used five processes, eight rounds, and two mirrored sweeps. All 26,880 trials and 564,480 full arrays passed. Independent Python validation matched 2,688 arrays and 6,544,608 elements. The archival pins checked the original ZIP, 202 Scope/DG artifacts, and 60 OLD_P2 artifacts against the original Git blobs and working files.

Default integration is **HOLD**. The only condition meeting all criteria was synthetic `oneway_dense` with legacy sources, q32, and ready preparation. The ratio was 0.7331 versus matched TABLE. With preparation it rose to about 1.31, and the distinct-source ready ratio was 1.3117. Google and LiveJournal showed no unique full-service advantage against strong controls. The API's `bound < n` fallback and a single output copy have separate effects from the guard. This campaign ended without another optimization round, MAIN integration, GPU execution, or paid resources. See `results/dg_api_20261021/` for raw logs, statistics, costs, and the executable bundle.

## Worktree and reading order

Use the `research/rcc` branch in a dedicated worktree. In the original layout, the RCC worktree was named `rcc` and the sibling `main` worktree tracked `main`. The upstream research workspace, `TCSC_RCC_RIE_CPU_STATIC_20261021`, is a read-only reference. The Git remote is `https://github.com/cudabinary/gpu-hwsw-research.git`.

Read [START_RCC_CODEX.md](START_RCC_CODEX.md), [RCC_STATUS.md](RCC_STATUS.md), [RCC_INTEGRATION_CONTRACT.md](RCC_INTEGRATION_CONTRACT.md), [RCC_NOVELTY_AUDIT.md](RCC_NOVELTY_AUDIT.md), and [SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md](evidence/previous/SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md) in that order. The handoff was prepared without starting a new chat.

## Algorithm and implementation

If source `s` belongs to the reachable set `R` of a previously completed BFS, then `Reach(s) ⊆ R`. TABLE stores a reachability bound per vertex. LAST retains the most recent owned result. Both update their state only after an exact, completed BFS. Partial traversals never produce a certificate. The search can stop at a safe row or level boundary once the number of distinct discovered vertices reaches the bound for its source.

The adapter is in `vendor/rcc_20261021/include/adapter.hpp`. Within that snapshot, `frozen/bridge/stop_bridge.hpp` connects the consumer, `frozen/rcc/` contains the original RCC implementation, `frozen/consumer/` holds the Direction traversal and builder, and `cuda/` contains the kernels and Windows host owner. The snapshot is hash-pinned. The shared CPU module in `src/cpu_module.cpp` wraps the existing RCC algorithm.

## Evidence and open questions

- The earlier CPU checks recorded 240,415 full-array comparisons and 988,173 assertions. The totals include checks beyond independent BFS executions.
- The independent Python check covered 1,836 arrays and 4,915,788 elements.
- The historical GPU pilot's stdout, receipt, and source, binary, and input hashes matched. It ran 12 processes, 36 BFS traversals, 12 cancellation checks, and 232 kernels in 14.907 seconds. Peak temperature was 44°C and the minimum observed free VRAM was 6,878 MiB. Its scope was correctness in the native owner.
- The full-service time ratio for Push+RCC TABLE versus Push+EARLY_N on LiveJournal at q32 was approximately 0.79991.
- RCC skipped zero additional edge checks and zero additional vertex checks after Direction+RIE in that LiveJournal configuration.
- The split initially lacked a matched full-service OLD_P2 comparison. The October 21 follow-up confirmed OLD_P2 as a strong resident and original-input ready baseline. The general winner remains **UNKNOWN**.
- The measurements did not establish an advantage for concurrent preparation over sequential preparation. Use the observed sequential winner where it wins.

## Completed follow-ups

The [extension audit](research/SCOPE_DISTANCE_AUDIT_RESULTS.md) and [novelty review](research/SCOPE_DISTANCE_NOVELTY_AUDIT.md) cover the separately supplied ZIP. The audit verified and rebuilt the package and confirmed additional candidate exclusion. It found limited synthetic ready gains with `oneway_dense` and no strong full-service gains on the tested real-world-derived inputs. The synthetic result failed with cold preparation or distinct sources. The original helper package had no shared-API plugin. The three existing API 1.0.0 modules passed substitution again. This earlier audit kept both extensions outside default RCC.

The [OLD_P2 comparison](research/OLD_P2_SERVICE_RESULTS.md) was completed in commit `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c`. It passed 672 trials and 14,112 full arrays across three processes, seven rounds, and two opposite sweep orders. With a ready reverse on the original LiveJournal input, RCC/P2 was 1.3045 at q8 and 1.0667 at q32. The attachment was still unopened at that checkpoint. See `results/old_p2_service_20261021/` for the raw data.

## Original follow-up plan at the split

The original plan called for completing the cold, deferred, and ready service comparisons with original OLD_P2 under the same owned-output contract before developing another algorithm. It specified Push+EARLY_N, Push+RCC TABLE, and OLD_P2 in matched runs on the original and relabeled LiveJournal inputs at q8 and q32. The preserved [baseline-gap document](evidence/previous/SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md) specifies the minimum retest. Compare records with equivalent timing boundaries. The worktree split included no new performance run.

Using a prior reachable set to narrow the next BFS's search scope remains a DISCOVERY candidate in [RESEARCH_CANDIDATES.md](RESEARCH_CANDIDATES.md). It needs evidence of incremental benefit, total cost, and performance against strong baselines before integration into default RCC.

## MAIN compatibility

The shared API 1.0.0 exposes `prepare`, `can_apply`, `run`, `update`, `invalidate`, and `release`. MAIN includes the API header only. A regression test loads the baseline, TABLE, and LAST dynamic modules into the same MAIN binary. The current evidence covers CPU functional compatibility. CUDA calls return an unsupported-backend error. Propose new versions to MAIN explicitly after regression and cost measurements. Integration requires an explicit merge decision.

## Tools and resumption

The original CPU environment used WSL, g++ 15.2 with C++20, Python 3, pthreads, and `dlopen`. Running `python3 tools/verify.py` writes to the current worktree's `build/` and `results/run_*`. For a static CUDA build, `tools/static_cuda.py` used nvcc 13.3 and MinGW. Keep binaries and logs isolated by worktree.

New GPU work requires a shared API backend, a finite dispatch budget, pinned source, binary, and inputs, current Windows PID/WDDM telemetry, at least 2,048 MiB free VRAM at startup and 1,536 MiB during execution, a temperature below 78°C, a 20-second child timeout and 300-second dispatch limit, and an independent watchdog. Stop on error and use zero retries and warmups. Historical permits and PID allowlists apply only to their original runs. Leave unrelated jobs running. Paid resources, paper branches, and submissions require separate authorization.

At meaningful checkpoints, review the diff, document evidence and limitations, commit, push to the authorized remote, and verify the remote SHA. Use forward-only updates and keep MAIN integration explicit. Check the most recent SHA with `git log -1` and the historical `DELIVERY_STATUS.json` receipt as applicable. Synchronization was performed during the session.
