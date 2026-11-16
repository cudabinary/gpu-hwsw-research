# Research worktree separation checkpoint

## Decision

The worktree split established separate tracks for MAIN GPU hardware–software research and RCC software evaluation. The existing `REDESIGN_PROBLEM` decision and the need for stronger baseline validation carried forward. The checkpoint introduced no algorithm or performance experiment.

## Source and Git preservation

The original task directory was outside Git. Two registered directories, labeled “Papers” and “Paper Source” here, each had an unborn `master` branch with no commit, remote, or tracked file. The migration preserved their names and state and copied their Git metadata separately.

A local ZIP preserved 10,270 research files, including large traces, in about 1.35 GB. CRC and SHA checks passed. The dedicated Git repository was initialized on `main` from an empty GitHub remote that was private at setup. The migration preserved existing Git history.

## Verification of historical evidence

The earlier CPU JSON recorded 240,415 comparisons, 988,173 assertions, and 1,836 arrays checked in Python. All 12 GPU stdout logs matched their receipts, including shutdown synchronization markers, and all pinned hashes matched. The historical pilot recorded 36 BFS runs, 12 cancellations, and 232 kernels in 14.907 seconds, with a 44°C maximum and at least 6,878 MiB free VRAM. The split reused those records.

On LiveJournal at q32, Push+RCC TABLE took approximately 0.79991 times the service time of Push+EARLY_N. RCC skipped zero additional checks after Direction+RIE. The strongest full-service path remains unknown because the original OLD_P2 was missing from the matched service comparison. That comparison was handed off to the RCC track.

## Shared API and module substitution

API 1.0.0 defines the lifecycle, graph identity and version, error and fallback behavior, and owned-result lifetime. The MAIN client uses the API without RCC implementation headers. The same executable loaded the baseline, TABLE, and LAST libraries. Each module passed 2,111 full-array comparisons covering 512 exhaustively enumerated graphs, duplicate edges, lifecycle cases, and four real inputs. Across three modules, 6,333 arrays matched. Assertion totals include edge parsing.

The suite covered exact fallback with no cache, a disabled cache, or an injected cache allocation failure. It checked rejection of mismatched graph instances, identities, or versions, invalidation, row-budget cancellation and pre-cancellation, certificate preservation on failure, repeated lifetimes, immutable readers, and rejection of unknown API versions. Required output allocation failures return an error and leave partial results private. Allocation failures were injected.

This checkpoint established CPU functional compatibility. The adapter's extra CSR and output copies and diagnostic counters have unmeasured performance costs. The CUDA API backend remains unimplemented and returns an unsupported-backend error. Actual per-GPU module substitution remains unverified. The historical pilot and static CUDA build have separate scopes.

## Research tracks

MAIN investigates GPU instruction, SM, cache, DRAM, and launch costs and the gaps in when information becomes available, how it is used, and when work can act on it. Algorithm development for RCC belongs in its own track.

RCC's priority is the OLD_P2 full-service baseline comparison. Retain module replaceability and evaluate novelty separately. Using a prior reachable set to narrow the next search remains a DISCOVERY candidate outside the default implementation. The evidence has yet to meet the `PAPER_CANDIDATE` or `PAPER_READY` criteria.

## Operational record

Other research and GPU processes continued running. This checkpoint ran zero new GPU queries, kernels, Nsight sessions, sanitizer runs, installations, or paid jobs. Historical approval flags remained inactive. Actual CUDA API verification requires a backend, a separate pinned plan, and fresh environment checks. See [GPU_COMPATIBILITY_GATE.md](GPU_COMPATIBILITY_GATE.md).

GitHub setup used Git Credential Manager's browser flow. The API confirmed the `cudabinary` account, private visibility at setup, and push permission. The initial remote listing succeeded and returned no refs. Tokens were kept out of files and chat. The external `DELIVERY_STATUS.json` receipt records the final branch SHAs and remote verification for this checkpoint.
