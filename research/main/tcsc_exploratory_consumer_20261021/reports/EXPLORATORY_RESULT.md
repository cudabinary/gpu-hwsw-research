# Actual GPU exploratory result -- ISOLATION_UNVERIFIED

The sole explicitly authorized exploratory session completed. This does not
change or erase the earlier strict HOLD_ENVIRONMENT result. The old module
guard and blocked capture are hash-verified unchanged. No protected-process
module/memory inspection, OS/security/driver/clock change, installation,
profiler, paid resource, extra dataset or automatic retry occurred.

## Execution and exact correctness

Nine CUDA workers completed: three micro7 smoke workers (modes7/8/5, sources
0/1/4) followed only after success by six LJ4096/48292 q32 workers in fixed
orders [7,8,5] then [5,8,7]. All201 complete distance arrays matched the C++
oracle and an independent Python byte comparison. These are201 unique GPU
results checked twice, not402 results. Three init-only cancellation checks
published no result. Each worker reported synchronized context release, exited,
and disappeared from the subsequent driver process list before another launch.

No CUDA error, observed discovery-capacity violation, watchdog or correctness
failure occurred. This is not an injected overflow test, race/sanitizer proof,
mid-kernel cancellation test or validation of the common RCC API GPU backend.
The immutable graph and repeated requests exercise the legacy experimental
owner; graph-mutation/generation rejection was not newly tested on GPU.

## Fixed descriptive timing

Same resident CSR/reverse, full distance initialization/return and owned output
boundary for every mode. q prefixes share one fixed batch; no online arrivals.
Validation/log/file output is outside the batch. The two orders are from one
non-isolated session, not independent sessions or a confidence interval.

| Mode | Order A q1 / q2 / q8 / q32 (ms) | Order B q1 / q2 / q8 / q32 (ms) |
|---|---|---|
| 7 lean static-bound Push | 0.6076 / 1.0901 / 4.8567 / 23.7695 | 0.5965 / 1.0927 / 4.8720 / 19.3772 |
| 8 equal-stop stats-Push | 0.6852 / 1.2713 / 5.6375 / 22.3687 | 0.6627 / 1.2448 / 5.5939 / 22.4061 |
| 5 Direction+zero+RIE | 0.8355 / 1.3692 / 5.4185 / 20.8163 | 0.8016 / 1.3475 / 5.4422 / 20.4316 |

Direction/lean-Push q32 changes winner between orders. Direction beats the
statistics-maintaining Push at q32 in both, but that is insufficient to beat
both strengthened baselines. At q1/q2/q8 Direction is slower than lean Push in
both orders. Every observation, including the adverse order, is retained. No
threshold, source, repetition or outcome was selected after observing results.

The current GPU harness is executable and exact on these tested cases. Stable
ready-consumer utility remains unresolved. Preparation-method causality,
preparation-inclusive service benefit, public strongest-SW superiority and HW
need are not established. No D0-D3 experiment was started.

## Timing/resource boundaries

Session wall: 13.016 seconds.
The summed CUDA-worker wall windows were 5.375 seconds, a conservative
GPU-usage window including host/setup/waiting, not GPU busy time. Reported query
stream-event intervals sum to 122.520 ms and contain host gaps; kernel busy time
was not measured. Python reference preparation was 0.047 CPU seconds. CPU reverse
build times total 1.5199 ms across nine workers. Context/H2D/handshake setup is recorded
separately in worker_raw.csv. No CPU duration is substituted for GPU conversion.

Peak observed temperature was 42 C; minimum free VRAM was 6839 MiB. These are37
sampled observations, not continuous extrema. Workspace payload was501,580 bytes
for LJ (32 MiB cap); driver/context/background memory is outside that payload.
The free-VRAM variation cannot be attributed solely to this worker.

There were32 initial C+G entries and two unreadable process names. They remain
unverified background, not an innocuous allowlist. Known research names, foreign
pure-compute contexts, positive foreign compute engines, new PIDs, required
telemetry failures and abrupt background3D changes would stop the session.
Sampling can miss short activity, graphics shares resources, and WSL coverage
is incomplete/UNKNOWN. Neither low utilization nor PID absence proves isolation.
Host scheduling, clocks, caching and unobserved contention remain uncontrolled.

## Next decision

The smoke/array gate is closed positively for these inputs and binaries. Stop
this finite session. Review the next bounded measurement contract jointly;
do not launch more to obtain a preferred outcome or proceed automatically to
builder/concurrency/HW experiments. The remaining utility question is whether
Direction reliably beats BOTH strengthened Push controls under an accepted
measurement contract. Timing here is exploratory only.
