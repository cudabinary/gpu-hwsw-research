# Session-regime audit: S1 versus S2/S3

**Recommendation: check the measurement regime before preparation-inclusive
evaluation.** The prepared Direction path became much shorter in the recorded
times, while lean Push did not become slower. Byte-identical code does not
make that an algorithm improvement. The records narrow the changed interval
but do not identify its physical cause.

This audit performed zero new GPU queries, CUDA runs, compilations, CPU
benchmarks or BFS correctness executions. It only captured and hashed existing
files and reaggregated their measurements. The original S1, S2/S3, strict guard,
RCC worktree and prior ZIPs were not modified. All sessions remain
ISOLATION_UNVERIFIED.

## Absolute times, with every reported pair retained

All values are q32 owned-output prefix milliseconds on the same 4096-vertex,
48292-edge LiveJournal-derived input and sources 17*i, i=0..31. Block labels
provide a descriptive arithmetic correspondence; they are not matched
experimental conditions across sessions.

| Session/block | Direction5 | Lean Push7 | D/P |
|---|---:|---:|---:|
| S1/0 | 20.8163 | 23.7695 | 0.87576 |
| S1/1 | 20.4316 | 19.3772 | 1.05441 |
| S2/0 | 11.2127 | 19.3911 | 0.57824 |
| S2/1 | 11.5136 | 19.3268 | 0.59573 |
| S3/0 | 10.8674 | 19.0618 | 0.57011 |
| S3/1 | 11.4575 | 19.0194 | 0.60241 |

Relative to the same S1 block label, Direction's new absolute time is
0.5221-0.5635 times the old time, a 43.65-47.79% reduction. Push's new time is
0.8019-0.9974 times the old time, a 0.26-19.81% reduction. Thus a worsening
denominator cannot explain the lower D/P ratios. Push's S1/0 is itself slower
than its S1/1; that order difference is retained, not discarded as invalid.

The exact arithmetic is R_new/R_old = (D_new/D_old)/(P_new/P_old), implemented
in `ABSOLUTE_CHANGE_VS_S1.csv`. This is not a causal decomposition. In
particular, the statement is that Direction's *recorded path time* fell, not
that a Direction optimization was made.

## Where the recorded time changed

`WORKER_COMPONENTS.csv` separates the prefix, stream-event interval sum,
output-allocation/copy sum, and their unallocated arithmetic remainder. The
event interval is not GPU busy/kernel time: the unchanged host loops issue
synchronizations, control copies and memory-safety checks between the events.
Host and CUDA event clocks also have different endpoints; the remainder is
not a separately measured host critical-path category.

| Direction comparison | Prefix decrease ms | Event-interval decrease ms | Output allocation/copy decrease ms | Unallocated decrease ms |
|---|---:|---:|---:|---:|
| S2/0 versus S1/0 | 9.6036 | 8.5060 | 0.8878 | 0.2098 |
| S2/1 versus S1/1 | 8.9180 | 8.0008 | 0.8146 | 0.1026 |
| S3/0 versus S1/0 | 9.9489 | 8.8718 | 0.8722 | 0.2049 |
| S3/1 versus S1/1 | 8.9741 | 7.9504 | 0.8934 | 0.1303 |

Most of the decrease is already present between the recorded events; it
cannot be explained solely by faster final D2H/output allocation. It is not
localized to one first-request outlier: all 128 descriptive Direction
request comparisons have lower `wall_ms`, and all five fixed descriptive
segments per comparison are lower. The segment partition was chosen for this
offline audit, not preregistered as a performance test. These comparisons reuse the same 64 S1
requests as references; they are not 128 independent experimental trials.
Direction's first delivered request changed from 0.8016-0.8355 ms to
0.4839-0.5104 ms, while the remaining 31-request mean changed from
0.6332-0.6445 ms to 0.3346-0.3558 ms. No outlier was removed.

The total reported launches stay 289 for Direction and 201 for Push. The
reported final per-request counters, levels, reasons and launch counts match;
the CPU-reconstructed edge-test totals stay 810522 and 1191634 respectively.
These are not GPU cache/DRAM traffic counts or proof of identical frontier
ordering/individual GPU accesses. Complete returned-output hashes also match.

## What is equal and what is not

| Item | Recorded comparison | Evidential limit |
|---|---|---|
| Executable, cubin, owner/driver/kernel/header/builder sources, input bytes | SHA-256 equal across S1 and S2/S3 | Excludes an edited algorithm/build artifact as the change; not all runtime state |
| Host compile | Existing receipt: C++17, -O2, -static, MinGW, CUDA 13.3 headers; output SHA matches both | Compiler version not recorded; no recompilation performed |
| CUDA compile | Same existing cubin in all sessions | Original CUDA compile flags absent from inspected session records; UNKNOWN |
| Per-mode argv | Equal after replacing the project root | Actual project/input/output paths differ |
| Explicit child environment assignments | Same source expressions, including CUDA_CACHE_DISABLE=1 | Full inherited environment and child echo were not recorded; UNKNOWN |
| Child working directory | Popen has no explicit cwd in either runner | Historical inherited cwd not recorded; UNKNOWN |
| Device/driver/model | RTX 4060 Ti, 610.88, WDDM in preserved snapshots | Does not prove same scheduling, clocks or exclusivity |
| Output/timing code | Identical owner source and executable | Host scheduling, cache state and event placement on the actual timeline unobserved |
| Warmup | Both plans declare zero warmups | Correctness smoke work precedes timing; this is not proof of cold caches/hardware |
| Cache control | Same cubin load and explicit driver-cache-disable source assignment | No measured L1/L2/DRAM cache residency or cache flush; UNKNOWN |
| Isolation | ISOLATION_UNVERIFIED in all records | External CUDA absence/WSL visibility UNKNOWN; never certified exclusive |

Owner SHA-256: `b9ebee00cfd5e45d336b37599672206c1e320c2b7be1f70497a8ae2c1fa1ef1b`.
Executable SHA-256: `fae72a0eb71507315058b90f6753fbe913e2c7ac914142037317d1ee852d44e7`.
Cubin SHA-256: `7cea25e119f9e1abbc583cb423db03db5d84f67c1b0dc02cc7170d3ef6b12836`.

The actual worker sequences differ:

- S1: smoke [7,8,5], timing [7,8,5]/[5,8,7].
- S2: smoke [5,7], timing [5,7]/[7,5].
- S3: smoke [7,5], timing [7,5]/[5,7], after a 60-second no-dispatch gap.

S1 included mode8 workers absent from S2/S3. The repeat runner also added
storage-quota scans, shorter session deadlines, a combined campaign deadline,
and S3 device/background-PID consistency checks. The parent observation/quota
work can overlap a child's timed interval. Its actual scheduling impact was
not measured; it is a hypothesis, not an explanation. Different session times
and process/background histories also remain confounds. These are related
exploratory campaigns, not exact replications to pool into a confidence interval.

## Setup and boundary

The identical owner loads the graph, completes a CPU reverse builder and runs
CPU oracle/replay before native setup. Context retain/module load/ready-ACK,
allocation, static-bound preparation and H2D finish before the query batch.
`context_setup_transfer_ms` is a mixed setup timer, not pure transfer time.
Every timing worker, including Push, allocates/uploads the complete reverse;
this is a ready-state comparison, not a minimized Push cold-service baseline.

For Direction, CPU reverse-build times are 0.2442-0.2504 ms in S1 and
0.2442-0.2642 ms in S2/S3. Native mixed setup increases from 170.99-175.19 ms
to 182.67-210.26 ms. Those setup values are excluded from the q32 prefix and
do not numerically account for its decrease. They could alter later state,
which was not measured. Graph-load, CPU validation and file logging are also
outside the prefix; logging occurs after the completed batch.

Inside the prefix are distance/event/counter initialization, kernels, level
synchronization, counter/error D2H, free-memory safety checks, event completion,
host output allocation and full distance D2H/publication. `batch_ms` differs
from the last prefix by at most 0.0001 ms in these logs due to the subsequent
batch endpoint/bookkeeping; no mixed-boundary ratio was used. Per-query and
setup values are supplied in the CSVs rather than subtracted into invented
GPU conversion/service costs.

Source anchors in the preserved `inputs/S1` snapshot:

- `src/owner_controls_v1.cpp:35`: reverse allocation/H2D and static metadata setup.
- `src/owner_controls_v1.cpp:59`: request wall timer; :64 begin event; :83 level sync.
- `src/owner_controls_v1.cpp:89`: end event; :92 output allocation/D2H; :94 publication.
- `src/owner_controls_v1.cpp:131`: graph/reverse/reference preparation.
- `src/owner_controls_v1.cpp:141`: native mixed setup; :145 owned-output prefix.
- `src/owner_controls_v1.cpp:148`: validation; :151 file output; :152 logging.
- `tools/run_exploratory.py:123`: filtered inherited environment and explicit overrides.
- `src/native_driver.hpp:25`: primary-context retain; :28 existing cubin load.

## Existing telemetry: available, but not request-aligned

This audit reparsed all 90 preserved XML samples, without executing nvidia-smi.
All samples report graphics/SM 210 MHz and memory 405 MHz. The recorded P-state
is P8 in all 37 S1 samples and all 26 S3 samples; S2 has 6 P8 and 21 P0 samples.
The published summary JSON had omitted clocks, but the raw XML contains them.
Thus clocks are not wholly absent; *actual clocks during each timed request*
remain UNKNOWN. The snapshots are not aligned with 10-24 ms timing batches or
individual kernels, and an owned PID indicates a context window, not a timed
kernel. Equal sampled clocks do not establish equal clocks during computation.
Neither the P-state distinction nor idle-looking clock readings prove a cause.

There is no per-request host scheduling, GPU launch timeline, cache-miss traffic,
memory-clock residency, enforced isolation or foreign-compute trace. No new
query can reconstruct those missing historical observations.

## One next-step recommendation

**Do not yet advance to preparation-inclusive evaluation. First resolve whether
the large unchanged-Direction timing regime difference is measurement/state
interference.** The finite existing records have reached their causal limit.
Keep both the favorable new signal and adverse S1 order intact. A separately
authorized, preregistered diagnostic would have to hold the complete worker/
smoke order, parent monitoring cadence, output boundary, environment capture and
setup history fixed and expose request-to-observation alignment. No such new
experiment or implementation was performed here, and this recommendation is
not permission to execute it. Do not tune until a desired winner appears.

Current evidence establishes neither a new preparation mechanism's contribution
nor a structural GPU bottleneck, hardware need, public strongest-baseline
advantage or general performance result. MAIN's final direction is unchanged.
