# GPU Hardware–Software Research

The main track studies structural GPU bottlenecks that persist after applying strong software baselines. The `research/rcc` branch develops reachability-certificate caching (RCC) for breadth-first search (BFS).

This checkpoint established separate worktrees and verified that the same CPU client binary can load the baseline, RCC TABLE, and RCC LAST modules through API 1.0.0. CUDA support for the shared API is pending. The historical GPU pilot used a native CUDA owner and tested correctness. Algorithmic novelty, performance gains from the shared API, and the need for new hardware remain open questions.

- [Shared API 1.0.0](api/rcc/v1.hpp)
- [Pinned RCC source snapshot](vendor/rcc_20261021/)
- [Earlier experiments](evidence/previous/)
- [Historical GPU verification](evidence/audit/HISTORICAL_GPU_VERIFICATION.json)
- [CPU compatibility results](results/COMPATIBILITY.json)
- [Reproduction instructions](REPRODUCE.md)

To run the CPU compatibility checks, run `python3 tools/verify.py` from the worktree root in WSL with g++ and Python 3. Each worktree keeps its own builds, logs, and outputs. Treat the original research workspace as read-only. GPU testing requires a separate backend implementation, validation, and current environment checks. Historical run approvals apply only to their original runs.
