# Implementation and contract boundary

Original MAIN/RCC worktrees and the frozen RCC snapshot are read-only inputs.
All changes are in this independent round directory. The source adapter starts
from a preserved base owner and a small replacement main. It never executes RCC
mode1. MAIN still has common RCC API1.0.0 CPU compatibility only; its CUDA backend
remains unsupported. This legacy experimental owner is not a new API backend.

Ready-consumer contract: immutable CSR and full CPU-built reverse, same graph
object/version, n<=4096, m<=131072, exact full distance array with -1 unreachable,
one owner submitting sequential requests, host-owned immutable output retained
across later requests/cancellation. All six modes allocate the same input CSR,
reverse, frontier/next/distance/control/bitmap payload before the timed batch.

Builder preparation is the frozen CPU independent::Builder. It is deliberately
unchanged. The source owner transfers its complete reverse to the GPU. This
validates neither a GPU builder nor a concurrent preparation publication path.
The static Job draft lacks an integrated GPU conversion owner, full transpose
output checks, failure-safe READY acquisition and reader-event retirement.

Minimum next implementation is not another queue-size experiment: a real GPU
conversion owner with same-builder D0/D1/D2/D3 dependencies, mandatory metadata
transfers, finite total allocation, exact reverse validation and complete error
handling. Existing readiness review estimates 5-8 files / 400-900 host/ABI/runner
lines. That is an estimate, not implementation done in this round. A native
Windows owner cannot directly link the existing Linux cuSPARSE .so. No install,
new builder, publication engine or cross-stream experiment was attempted.

If ready B later proves useful, include a strong eager-construction+reuse path
and report same-builder causality separately from the strongest practical SW.
Lazy preparation is not invented here. Initialize/allocate/maintain/synchronize,
fallback, full output return and total memory must remain in service accounting.

The timing-only Push is the strongest current internal frontier-queue kernel,
not a proof against public load-balanced GPU BFS. All modes retain EARLY_N;
frontier-zero is evaluated before incremental RIE. Algorithmic edge-test replay
is not L2/DRAM traffic, occupancy or GPU resource attribution. Its GPU trajectory
cross-check has not run because the session stopped before the first worker.
