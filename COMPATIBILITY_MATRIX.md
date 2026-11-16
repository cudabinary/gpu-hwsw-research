# Compatibility evidence

| Check | CPU API 1.0.0 | CUDA API 1.0.0 |
|---|---|---|
| Exact fallback when disabled or no certificate is available | PASS | Pending implementation |
| Full arrays and baseline swap with RCC enabled | PASS | Pending implementation |
| Rejection of mismatched graph identity, version, or instance | PASS | Pending implementation |
| Invalidation and preparation after a graph change | PASS | Pending implementation |
| Pre-cancellation, row budget, and private partial state | PASS | Pending implementation |
| Injected cache and output allocation failures | PASS | Pending implementation |
| Repeated requests and readers that outlive release | PASS | Pending implementation |
| Shared TABLE/LAST interface and rejection of unknown API versions | PASS | Pending implementation |
| Same client results across MAIN and RCC worktrees | See the final `CROSS_WORKTREE.json` | Unverified |
| Backend capability reporting | Reports CPU support | Reports CUDA unavailable and rejects CUDA requests |

Dynamic modules require a matching toolchain ABI and remain loaded throughout the process. Coverage is limited to the current compiler ABI and API 1.0.0. Future RCC v2/v3 interfaces remain untested.

The historical CUDA owner passed 36 BFS runs and 12 cancellation checks. The static build of the preserved copy provides separate compile and link evidence. Shared CUDA API compatibility requires a backend that passes the applicable tests.
