# GPU Hardware–Software Research

The main track studies structural GPU bottlenecks that persist after applying strong software baselines. The `research/rcc` branch develops reachability-certificate caching (RCC) for breadth-first search (BFS).

This checkpoint established separate worktrees and verified that the same CPU client binary can load the baseline, RCC TABLE, and RCC LAST modules through API 1.0.0. CUDA support for the shared API is pending. The historical GPU pilot used a native CUDA owner and tested correctness. Algorithmic novelty, performance gains from the shared API, and the need for new hardware remain open questions.

The [matched OLD_P2 follow-up](research/OLD_P2_SERVICE_RESULTS.md) compared full service under the same owned-output contract. On the original LiveJournal input, RCC lost to OLD_P2 when the reverse index was already available. The ranking depended on the fixture and preparation boundary.

The [independent RCC-Scope and DistanceGuard audit](research/SCOPE_DISTANCE_AUDIT_RESULTS.md) verified the original ZIP and 92 manifest entries, rebuilt the prototypes, and reproduced additional probe savings. Across 16 policies, the only result meeting the full performance criteria was a synthetic ready condition. It lost when preparation was included or distinct sources were used. The audit left default RCC, the shared API, and MAIN intact. See the [prior-work assessment](research/SCOPE_DISTANCE_NOVELTY_AUDIT.md).

A later [experimental DistanceGuard plugin](research/DG_API_RESULTS.md) passed CPU module substitution using the existing MAIN binary. Default integration remains on hold. The tested real-world-derived graphs did not establish a speed advantage over strong, matched controls.

- [Shared API 1.0.0](api/rcc/v1.hpp)
- [Pinned RCC source snapshot](vendor/rcc_20261021/)
- [Earlier experiments](evidence/previous/)
- [Historical GPU verification](evidence/audit/HISTORICAL_GPU_VERIFICATION.json)
- [CPU compatibility results](results/COMPATIBILITY.json)
- [Reproduction instructions](REPRODUCE.md)

To run the CPU compatibility checks, run `python3 tools/verify.py` from the worktree root in WSL with g++ and Python 3. Each worktree keeps its own builds, logs, and outputs. Treat the original research workspace as read-only. GPU testing requires a separate backend implementation, validation, and current environment checks. Historical run approvals apply only to their original runs.
