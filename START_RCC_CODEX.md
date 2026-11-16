# Start an RCC Codex session

In Codex, open the local worktree for `research/rcc` and start a chat there. The original handoff did not create a chat or send instructions to another research session.

Suggested initial prompt:

> This is the `research/rcc` worktree of `gpu-hwsw-research`. Read `AGENTS.md`, `HANDOFF_RCC.md`, `RCC_STATUS.md`, `RCC_INTEGRATION_CONTRACT.md`, `RCC_NOVELTY_AUDIT.md`, and `evidence/previous/SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md`. Verify the worktree state and remote SHA. Treat the upstream workspace and MAIN as read-only. Preserve API 1.0.0 and the module-substitution regression suite. First, review the missing full-service comparison with OLD_P2 under the same output contract and define a bounded experiment. The winner against the strongest baseline remains open. Keep the proposed reachable-set pruning at DISCOVERY and outside default RCC. Report CPU compatibility, the historical native GPU pilot, and shared CUDA API compatibility according to their individual test scopes. Before GPU backend and execution work, verify the finite budget, current environment checks, and authorization. Commit the evidence and limitations, push to the authorized remote, and verify its SHA. MAIN merges and paper branches require an explicit decision.

On another computer, resolve repository paths from the root of the RCC worktree.
