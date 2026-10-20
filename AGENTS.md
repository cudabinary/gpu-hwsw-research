# Research operating rules

- Preserve `vendor/rcc_20261021` byte-for-byte; pin changes require explicit provenance and regression evidence.
- Read `TRACK_STATUS.md`, `RCC_INTEGRATION_CONTRACT.md` and `HANDOFF_RCC.md` before changing research code.
- MAIN uses only `api/rcc/v1.hpp`. Do not include RCC implementation headers from MAIN clients.
- RCC algorithms evolve on `research/rcc`; no automatic merge into MAIN.
- Keep API versioning, exact fallback, owned immutable outputs, graph identity/version checks and negative tests.
- Run `python3 tools/verify.py` for common contract changes. Do not declare CUDA compatibility from CPU tests or historical pilot results.
- No force push, history rewriting, deleting another worktree, stopping unrelated jobs or paper-branch creation without authorization.
- Each worktree owns its build/log/output directories. Do not share mutable artifacts across worktrees.
- Research checkpoints require evidence, claims/limitations, a local commit, authorized push and remote SHA verification. Session end does not establish background synchronization.
- New GPU work must have an explicit finite run ledger and fresh PID/VRAM/temperature/watchdog checks. A past permit is not a reusable run token. No paid resources by implication.
