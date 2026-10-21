# Ready-consumer discrimination round

The question is whether an already prepared reverse graph improves exact GPU
BFS consumption relative to this repository's frontier-queue Push+EARLY_N.
This is not a test of independent GPU construction or new hardware necessity.

Before observing performance, fix LJ4096/48292 and Google1024/6692, sources
0,17,...,527, three paired blocks, six modes, alpha=15 and beta=24. Google is a
preselected negative/control input, not a searched positive workload. The six
functional micro processes precede 36 ready timing processes. Maximum: 42 CUDA
workers, 1170 complete BFS arrays and six initialization-only cancellation tests.
The existing kernel source/cubin is unchanged; only its host owner is adapted.
RCC mode1 is excluded. No library installation, Nsight, sanitizer or GPU builder.

Modes: Push+EARLY_N; Direction+EARLY_N; Direction+RIE; Direction+frontier-zero;
Direction+frontier-zero+RIE; and forced Push with the same policy counters.
EARLY_N is present in every mode. Frontier-zero uses already maintained exact
frontier outgoing-degree sum. It precedes RIE so a shared stopping boundary is
not attributed to incremental RIE value. This is an ordinary static stop guard,
not a new BFS algorithm. Direction policies and CPU-built reverse are frozen.

Every mode starts with identical resident CSR, full reverse and bitmap allocation.
The baseline has access to the same immutable information from the start.
Native device allocation bytes include input CSR, final reverse and workspace;
driver/context use is additionally constrained by total free-VRAM monitoring.
All queries initialize their state, synchronize/check errors and return a complete
owned host distance array. Allocation/transfer/context setup and CPU reverse
construction are recorded separately from ready consumption. They are not a
measured GPU builder or pure GPU conversion cost.

q1/q2/q8/q32 are timestamps in one fixed q32 batch, not independent experiments
or an online arrival process. Reference BFS and deterministic work replay happen
before CUDA initialization. Validation, binary array capture and logging occur
after the batch. Actual D2H and owned output publication remain in each query.
Work counts are code reconstruction checked against GPU seen/level/termination
state and exact arrays, not sampled GPU memory transactions or Nsight counters.

Primary exploratory gate: LJ mode5/mode0 q32 ratio below 0.95 in all three blocks.
Report every mode, input and q prefix regardless of outcome. Three blocks in one
session cannot establish 1% noninferiority, broad GPU generality or confidence
about small effects. No threshold search, positive-input search or extra repeats.
This internal Push uses one thread per frontier vertex and serial row traversal;
it is not a demonstrated best public load-balanced GPU BFS implementation.

If ready B is not useful, stop preparation expansion for this input/contract.
If useful, it supplies a preparation-cost target only. D0/D1/D2/D3 require a real
GPU builder owner, READY publication/reader retirement and full transpose checks.
The current static Job draft lacks that integration. Do not substitute CPU build
times or old 18.92% interference for a new GPU preparation measurement. Stop at
that implementation boundary rather than starting a new builder campaign.

Safety: fresh native PID/module/engine/LUID baseline plus WSL maps guard; start
free>=2048MiB, runtime free>=1536MiB, temperature<78C, freshness<=3s. Independent
PID+creation-time watchdog20s plus parent timer. Dispatcher<=900s and the whole
GPU session<=1800s. On mismatch, OOM, competing/unknown GPU activity, watchdog or
guard failure, stop without retries or relaxing the rule. Only owned helpers may
be terminated. Process exit and context-release marker/PID disappearance are
required before another CUDA worker. A watchdog cannot guarantee preemption of
a single running kernel. No new research direction or hardware claim is adopted.
