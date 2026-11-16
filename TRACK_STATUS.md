# MAIN track at the worktree split

- **Goal.** Identify structural bottlenecks that persist after strong GPU software optimizations and evaluate opportunities for hardware–software co-design.
- **Branch.** Use `main` from the repository root.
- **Checkpoint.** The original work was preserved, MAIN and RCC were split into separate worktrees, and the CPU API 1.0.0 module swap passed regression testing.
- **Open claims.** GPU performance advantage, shared CUDA API compatibility, the need for new hardware, and RCC novelty remain unverified.
- **Next steps.** See [MAIN_NEXT_RESEARCH.md](MAIN_NEXT_RESEARCH.md). Incorporate the RCC track's OLD_P2 service comparison after review. MAIN integration requires an explicit merge.
- **Worktree isolation.** Write builds, logs, and outputs inside this worktree.
- **Remote verification.** Use the historical `DELIVERY_STATUS` receipt and `git ls-remote` to check the recorded push and current branch SHA, respectively.
