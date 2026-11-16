# RCC independent track

**Latest checkpoint.** The experimental DistanceGuard API 1.0.0 plugin passed substitution in the existing MAIN binary without a rebuild. The only qualifying full-service result was synthetic `oneway_dense` with legacy sources at ready q32. It reversed when preparation was included. The tested Google and LiveJournal cases established no unique full-service advantage against strong controls. Default integration is on hold. The campaign ended with zero additional optimization rounds, GPU jobs, or paid jobs. [DistanceGuard API results](research/DG_API_RESULTS.md)

- **Goal.** Independently verify correctness, full service cost, incremental improvement over strong software, and novelty for default RCC and proposed extensions.
- **Worktree.** Use branch `research/rcc` from the repository root. MAIN has a separate worktree.
- **Completed.** Preserved original sources, verified the original three CPU API modules in the same MAIN binary, closed the OLD_P2 comparison gap, and independently audited the supplied RCC-Scope and DistanceGuard package.
- **Open claims.** GPU performance, CUDA API compatibility, the need for hardware, and research novelty remain unverified.
- **Earlier extension audit.** Candidate helper compatibility was still open before the subsequent plugin experiment. The two helpers remained standalone candidates. [Implementation audit](research/SCOPE_DISTANCE_AUDIT_RESULTS.md)
- **Local outputs.** Write builds, logs, and outputs within this worktree. MAIN changes and merges require a separate decision.
- **Remote verification.** Check the locally retained, historical `DELIVERY_STATUS.json` receipt and use `git ls-remote` for the current branch SHA. The receipt is stored outside the commit to avoid self-reference.
