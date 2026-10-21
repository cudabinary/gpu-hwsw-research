# CPU follow-up of existing GPU timing records

No new GPU query, execution, compilation, BFS validation or tuning occurred.
This analysis reads the six preserved LJ timing workers:192 requests, two
orders, one measurement session, contract ISOLATION_UNVERIFIED. The three micro
smoke workers are correctness evidence, not timing repetitions. No confidence
interval or stable-performance claim is supported by this repetition count.

## Full owned-output prefixes

Values below are milliseconds. A is execution order [7,8,5]; B is [5,8,7].
All q values are nested prefixes of the same32-source batch, not independent
experiments or online-arrival measurements.

| q | Lean Push7 A / B | Stats Push8 A / B | Direction5 A / B |
|---|---:|---:|---:|
| 1 | 0.6076 /0.5965 | 0.6852 /0.6627 | 0.8355 /0.8016 |
| 2 | 1.0901 /1.0927 | 1.2713 /1.2448 | 1.3692 /1.3475 |
| 8 | 4.8567 /4.8720 | 5.6375 /5.5939 | 5.4185 /5.4422 |
| 32 | 23.7695 /19.3772 | 22.3687 /22.4061 | 20.8163 /20.4316 |

Direction is slower than lean Push at q1/q2/q8 in both orders. At q32 it is
12.424% faster in A and5.441% slower in B. Against the more expensive statistics
Push, q32 Direction is faster by6.940% and8.812%; that does not establish a win
against lean Push. Mean prefix/q values in the CSV are descriptive amortized
costs, not per-request latency distributions from repeated identical requests.

`request_timings_192.csv` gives each actual query wall time, delivered increment,
stream interval and output-allocation/copy time. The delivered increment is the
difference between adjacent owned-ready prefixes, including outer-loop work;
`query_wall_ms` is the owner's inner query bracket. Their small differences are
retained rather than silently equated.

## What changed between the two orders?

| Mode | B minus A q32 | Relative B/A change |
|---|---:|---:|
| Lean Push7 | -4.3923 ms | -18.479% |
| Stats Push8 | +0.0374 ms | +0.167% |
| Direction5 | -0.3847 ms | -1.848% |

All96 same-source/mode comparisons have equal recorded seen/level/kernel counts
and reconstructed edge tests. Lean Push's largest single request difference
is query21/source357: B minus A=-0.3861 ms; the other31 requests contribute
-4.0062 ms. The q32 reversal cannot be removed by dropping one uniquely large
request. No request or order was removed and no trimmed result is substituted.
Temporal drift, scheduling, clock/cache state and background contention are
not separately identified. Execution position and time are confounded with
order; this table does not prove a causal order effect or a GPU resource cause.

## Exact timing boundaries

The pinned source locations are recorded in TIMING_BOUNDARIES.json.

| Component | Owned-ready prefix / query wall | Other recorded boundary / limitation |
|---|---|---|
| File read and original CSR construction | Outside | `graph_load_ms`; CPU file/CSR work |
| Reverse COUNT/scan/scatter/verification and its allocations | Outside | `cpu_reverse_build_ms`; CPU builder only, not GPU conversion |
| Independent CPU oracle/replay | Outside | `cpu_reference_and_work_replay_ms`; research validation overhead |
| Native context/module setup and parent ACK | Outside | In composite `context_setup_transfer_ms`; not separately isolated |
| Device allocation; original CSR/reverse H2D | Outside | Same composite setup field; H2D-only and allocation-only times UNKNOWN |
| Common K-bound scan | Outside | `static_bound_setup_ms`, a subset of setup time; do not add twice |
| Source/owner/graph checks before the inner query clock | Inside prefix | Outside inner `query_wall_ms`; retained in delivered increments |
| Device distance initialization and per-level counter/bitmap initialization | Inside | Kernel/memset cost not separately timed |
| First-use per-kernel function-handle lookup | Inside | Lazy `cuModuleGetFunction` in launch helper; different consumer kernels can affect q1 |
| Events, level stream synchronization, control D2H, error checks and free-memory safety calls | Inside | Safety remains enabled; fewer levels remove these costs too |
| Host output vector allocation/zero initialization and full distance D2H | Inside | `return_copy_ms` includes allocation AND copy, not pure DMA time |
| Owned output publication and loop bookkeeping | Inside prefix | Inner query wall ends slightly before outer-loop prefix record |
| Full-array validation and log/binary-file saving | Outside | Post-batch validation separately recorded; no unrecorded service zero assumed |
| Final owner cleanup/context release | Outside prefix | Verified after the batch; included in the broader worker window |

Stream-event intervals span a stream timeline containing host submission/sync
gaps. They are neither summed kernel busy time nor a component to add again
to query wall. The broader worker windows include process/setup/waiting and
cannot be substituted for a production cold-service duration. Composite setup
includes experiment-specific handshake delay; it is not reverse preparation.

## Sequential versus concurrent preparation is UNKNOWN

The only preparation path here is CPU reverse construction before GPU setup.
Both Push controls also receive the full resident reverse to equalize ready
state. No Plan A-only, GPU P-only, A->P or A||P run exists in this round; no
P_READY/joint-ready timing or interference measurement was recorded. There is
no no-reverse service baseline, GPU builder or conversion-only measurement.

Adding CPU build time to a ready prefix would describe neither GPU sequential
preparation nor concurrent service. Adding setup mixes context/ACK/transfer
costs; taking max(A,P) assumes overlap and independence that were not observed.
Thus sequential joint-ready, concurrent joint-ready, A interference, remaining
GPU preparation time and q1/q2/q8/q32 preparation-inclusive service comparisons
remain UNKNOWN. No CPU estimate replaces an existing GPU measurement.

Mode7 requires only the static certificate during queries, whereas this harness
still builds/transfers the whole reverse for every mode. A real full-cost
comparison must charge certificate metadata versus full-reverse construction
and every mandatory allocation/transfer/synchronization/output, once. The
present equal-ready-state experiment deliberately does not answer that question.

## Remaining question and bounded request

The unresolved question is whether Direction can reproduce a q32 benefit over
the strongest tested lean Push at the same full-distance return boundary,
while retaining its q1/q2/q8 disadvantages. These are internal baselines, not
a claim against the best public load-balanced GPU BFS implementation.

GPU_APPROVAL_REQUEST.md proposes only two additional, separately started,
counterbalanced sessions of modes7/5 on this same input and sources. Mode8's
current data remain preserved; a comparison with mode7 alone cannot establish
dominance over every other baseline. No new kernel/builder/parameter search,
profiling or preparation overlap is proposed. A consistent prospective signal
would justify review only, not erase the old opposite outcome or establish HW
need. Further mixed results leave ready utility unresolved and preparation
expansion on hold. The request is not executed or approved by this document.
