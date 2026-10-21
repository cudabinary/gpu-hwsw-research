# Approved S2/S3 exploratory repeat: result

Exactly the two newly approved local RTX 4060 Ti sessions completed. No third
session, new input, tuning, kernel, build, profiler, sanitizer, installation,
paid resource, source deletion or OS/security/clock change was performed.
The measurement contract remains ISOLATION_UNVERIFIED; strict mode and the
earlier blocked capture remain unchanged. All source/binary/input pins match.

## Actual execution

Twelve CUDA workers completed 268 BFS requests, each full distance array checked
by C++ and independent Python. These are 268 requests checked twice, not 536.
Four init-only cancellation checks published no output. Kernel submissions
including these cancellations: 2036. No CUDA error, OOM, full-output mismatch,
watchdog or observed-environment stop occurred. Every worker reported synchronized
context release, exited and disappeared from the subsequent driver PID list.
This does not certify mid-kernel cancellation, sanitizer safety, injected queue
overflow or graph-mutation handling; it is the existing consumer-owner contract.

S2 smoke was [5,7], then timing [5,7]/[7,5]. S3 smoke was [7,5], then timing [7,5]/[5,7].
Smoke q3 sources were 0/1/4; timing q32 sources were 17*i, i=0..31, unchanged.
The 60-second no-dispatch gap followed S2 retirement/helper cleanup. Whole
campaign wall including the gap and session cleanup was 82.390 seconds (<600).
New worker windows sum to 7.515 seconds; these include host/setup/waiting,
not GPU busy time. Query stream-event intervals sum to 116.445 ms and contain
host gaps. CPU reverse builds sum to 2.0300 ms; independent Python reference
preparation sums to 0.109 CPU seconds. None is substituted for GPU conversion.

Across 53 management snapshots, peak observed temperature was 42 C and
minimum free VRAM was 6839 MiB. These are sampled extrema, not continuous guarantees.
LJ device payload remained 501,580 bytes (32 MiB request cap). Driver/context
and background allocation is additional. Raw result bytes recorded at campaign
completion: 8987550 (<128 MiB); derived reports are separate.

## Every order retained

| Session / block | Push7 q1 /q2 /q8 /q32 ms | Direction5 q1 /q2 /q8 /q32 ms | q32 D/P |
|---|---|---|---:|
| S1/0 | 0.6076 / 1.0901 / 4.8567 / 23.7695 | 0.8355 / 1.3692 / 5.4185 / 20.8163 | 0.87576 |
| S1/1 | 0.5965 / 1.0927 / 4.8720 / 19.3772 | 0.8016 / 1.3475 / 5.4422 / 20.4316 | 1.05441 |
| S2/0 | 0.5971 / 1.1031 / 4.9169 / 19.3911 | 0.5104 / 0.8334 / 3.0845 / 11.2127 | 0.57824 |
| S2/1 | 0.5878 / 1.0908 / 4.8727 / 19.3268 | 0.4839 / 0.8225 / 3.0933 / 11.5136 | 0.59573 |
| S3/0 | 0.5830 / 1.0622 / 4.6355 / 19.0618 | 0.4959 / 0.8074 / 2.9961 / 10.8674 | 0.57011 |
| S3/1 | 0.6673 / 1.1251 / 4.8145 / 19.0194 | 0.4849 / 0.8118 / 3.1012 / 11.4575 | 0.60241 |

All four prospective q32 Direction/Push7 ratios are below the predeclared 0.95
exploratory margin. New q1/q2/q8 prefixes also favor Direction in all four pairs.
This is a consistent prospective signal on this one input/contract. The old
S1 negative order and its short-prefix losses remain visible above; they were
not trimmed, replaced or reclassified. S1 mode8 records remain preserved but
were not rerun under this approval. No dominance over mode8 in the new sessions
or over a public strongest GPU BFS implementation is established.

There was no algorithm/binary/input change that explains the large Direction
time change from S1 to S2/S3. Logical level/kernel/work trajectories match the
frozen contract. New orchestration adds quota and campaign-deadline checks;
graphics/host scheduling, clocks, caches and other unobserved contention can
also differ. The reason is UNKNOWN. The new consistent pairs are not a proof
that the old adverse result was invalid. Do not pool these different regimes
into a confidence interval or claim final stable/general performance.

## Boundary and limits

Timing is ready-resident consumption, not whole preparation/service. CPU graph
load/reverse construction and native setup/H2D precede the query batch and are
recorded separately. Native setup also includes context/ACK/allocation costs;
it is not pure transfer time. Query distance initialization, events, counter/
bitmap initialization, level sync/control copies/free-memory safety checks,
host output allocation, full D2H and owned publication remain inside timing.
Validation and logging follow the batch. No safety check was disabled for speed.

External CUDA absence and WSL context visibility remain UNKNOWN. Initial C+G
background entries and unreadable names were not inspected via process memory
or modules. Low utilization/PID absence is not isolation proof. No hardware
counter or kernel timeline was collected. The experiment cannot attribute
memory/SM/control bottlenecks or our preparation method's causal contribution.

No GPU builder, Plan A/P joint-ready, D0-D3 or preparation-inclusive q-service
experiment ran. Those costs and HW necessity remain UNKNOWN/unestablished.
The new signal supplies a reason to REVIEW a separate full-cost question,
not permission to build/run it or change MAIN's research direction. This finite
approval is consumed. Stop and hand off the original evidence and all ratios.
