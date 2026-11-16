# Completed, separately authorized GPU correctness pilot

The work began with a CPU and static-build scope. The user later explicitly authorized the bounded GPU pilot recorded here. Earlier F/P1/P2 permits remained inactive. The execution manifest, `config/GPU_MINIMAL_PILOT.json`, retains the source, binary, input, and monitor hashes.

- The pilot checked whether EARLY_N, RIE, and RCC preserve complete distance arrays under GPU level publication and source switching.
- Inputs were micro7 (duplicates, self-loop, disconnected component, and sink), LiveJournal4096, and synthetic scc4_d32.
- The four modes per input were PUSH_N, PUSH_RCC_TABLE, DO_N, and DO_RIE, for 12 processes.
- Each process ran three complete BFS traversals, including the initial certificate setup where applicable, and one explicit cancellation. The total was 36 BFS runs plus 12 cancellations, or 48 calls.
- Limits were 300 seconds overall, 20 seconds per child, 32 MiB of workspace, at least 2,048 MiB free VRAM at startup and 1,536 MiB while running, and temperature below 78°C.
- The run used zero warmups, retries, Nsight Systems or Compute sessions, sanitizer runs, installations, external downloads, and paid GPU jobs.
- The pilot stopped further dispatch on a graphics PID outside the pinned allowlist, ambiguous or stale telemetry, a CUDA error, a distance mismatch, a watchdog trigger, or a VRAM or temperature violation.
- Further GPU execution required confirmed context release.

All 12 processes passed in 14.91 seconds. Candidate next steps were uninstrumented, paired consumer measurements with the same owner and a separate experiment for the end-to-end GPU service. The pilot included an intermediate cancellation check, CPU reverse construction, and host validation. Its measured scope was correctness. The campaign ended after completing the bounded CPU measurements and GPU pilot.
