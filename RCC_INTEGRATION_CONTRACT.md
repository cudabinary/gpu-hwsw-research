# RCC integration contract 1.0.0

[The API header](api/rcc/v1.hpp) defines the integer ABI ID `0x00010000`. The current implementation supports CPU dynamic modules built with g++ and C++20 on WSL Linux. CUDA requests return `UNSUPPORTED_BACKEND`.

## API semantics

- `prepare(graph, options, seed_source=-1)` releases the previous binding and prepares a CSR copy, workspace, and certificate storage. If a seed is supplied, it runs a complete BFS to build a certificate. `prepare_ns` includes that cost.
- `can_apply(graph, source)` checks for the same immutable graph instance, identity, and version, and for a valid reachability bound smaller than `n`. A bound of `n` provides no useful certificate.
- `run(request)` returns a complete distance array as an owned, immutable `Output`. A distance of `-1` means unreachable. The module updates certificates only for completed results. With no certificate, a disabled cache, or a cache allocation failure, it runs exact Push+EARLY_N.
- `update(request)` runs a complete BFS from the requested source and updates certificate state. It certifies results it computes itself. `update_ns` accounts for computation, copying, and publication as in `run`.
- `invalidate()` clears certificate state. Outputs held by existing readers remain valid.
- `release()` releases module-owned resources and the graph binding. Previously returned outputs retain their graph and distance storage independently.

The module rejects a different `Graph` instance even if its identity and version strings match. To change graphs, pass a new immutable object with an incremented version to `prepare`. A graph mismatch returns `INVALID_GRAPH`. After preparation, the new graph can use exact baseline BFS.

## Failures, cancellation, and publication

A single owner calls the module sequentially. Other threads may read already published immutable outputs. Concurrent cache writers and lock-free publication are outside the contract. Pre-cancelled requests return immediately. The row budget triggers cancellation checks at row boundaries. Cancellation exposes neither partial output nor a certificate, and a retry starts a fresh traversal.

The adapter allocates published output storage before the legacy executor updates its certificate. The subsequent distance copy performs no additional allocation. The legacy executor also allocates its complete output before updating its certificate. Cache allocation failure triggers exact baseline fallback. Failure to allocate required graph, workspace, or output memory returns an explicit error.

## Module substitution, versioning, and lifetime

MAIN uses the API header and the `Graph` contract. It selects a library that exports `rcc_create(version)` and `rcc_destroy()`. TABLE and LAST are internal to their modules. The `baseline-1`, `rcc-table-20261021-v1`, and `rcc-last-20261021-v1` modules implement the same API and wrap existing algorithms.

The ABI requires matching OS, architecture, compiler, and C++ runtime builds. The factory rejects unknown API versions. Dynamic libraries stay mapped for the life of the process because an `Output` can retain a `shared_ptr` deleter from its module. Tests cover readers that outlive module release or destruction. Arbitrary library unloading is outside the contract.

Future implementations must satisfy the same contract and regression suite. Breaking changes require a new major version, a distinct API ID, and an explicit migration adapter. API v2 has no implementation or compatibility results yet.

## Measurement boundaries and support

The module reports `prepare_ns`, `run_ns`, `update_ns`, examined edges, cache payload, additional CSR payload, and the number of elements copied into the output. The adapter copies the original CSR into legacy storage, performs one additional copy into the owned output, and uses `Trace=true` for diagnostics. The payload accounting excludes items such as temporary edge pairs, workspace, allocator metadata, and RSS. The earlier CPU ratio of approximately 0.80 applies to the original path. Service performance with the adapter's extra costs remains unknown.

The CPU compatibility results, static CUDA build, and historical GPU pilot support different claims. Actual CUDA API substitution, graph lifetimes, allocation failures, and cancellation still require validation.
