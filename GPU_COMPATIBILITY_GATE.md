# CUDA compatibility gate

The shared API 1.0.0 reports `Capabilities.cuda=false`. Calling `prepare(backend=CUDA)` returns `UNSUPPORTED_BACKEND`. The CPU contract suite verifies this rejection. The shared CUDA backend remains unimplemented and unverified.

The historical pilot for the preserved CUDA owner and kernels passed 36 BFS runs and 12 cancellation checks. Its stdout was checked against the pinned source and binary hashes. The preserved CUDA code also compiled and linked statically. Shared API integration requires separate validation.

The backend still needs an adapter from the native owner to the shared API lifecycle, a fully owned distance result, graph identity and version checks, a reuse policy after cancellation or errors including out-of-memory failures, library and driver lifetime handling, exact baseline fallback, and clearly defined instrumentation costs.

Once the backend exists, pin the source, binary, and inputs before finalizing a validation plan. The proposed ceiling matches the earlier pilot at 12 processes, 36 BFS runs, and 12 cancellation checks across three inputs (`micro7`, `LJ4096`, and `scc4_d32`) and four validation paths. The proposed limits are 20 seconds per child, 300 seconds total, 32 MiB of workspace, 2,048 MiB free VRAM at startup, 1,536 MiB free during execution, and a temperature below 78°C. Use zero warmups and retries. Each path checks baseline/RCC substitution, identical distance arrays, private partial state on cancellation, and a fresh run afterward. The backend SHA and exact kernel count remain open. This proposal requires separate authorization before execution.

The plan requires current PID/WDDM, VRAM, and temperature checks, an independent watchdog, and confirmation that CUDA work has ended after exit. Stop further dispatch on unrelated compute activity, uncertain telemetry, runtime errors, correctness failures, watchdog triggers, or memory or temperature violations. The proposal excludes Nsight and paid resources.
