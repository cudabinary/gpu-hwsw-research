# Separate exploratory GPU consumer round, 2026-10-21

**ISOLATION_UNVERIFIED. Actual GPU correctness passed; timing is mixed and
exploratory. No isolated-performance, preparation-causality or HW claim.**

Read reports/EXPLORATORY_RESULT.md and results/analysis/SUMMARY.json first.
The sole session completed nine processes,201 complete BFS arrays and three
init-only cancellation checks. Both C++ and independent Python verified each
array. These are201 unique GPU results, not402. Session wall was13.016 seconds;
summed worker windows were5.375 seconds. Observed temperature peaked at42 C and
free VRAM stayed at or above6839 MiB. Stream-event intervals are not kernel busy time.

The explicit new user authorization permits this separate non-isolated mode.
It does not change Windows security, privileges, driver/clock settings or the
old strict guard. The old HOLD_ENVIRONMENT capture and strict code remain
hash-verified unchanged. This mode does not inspect protected/foreign process
modules or memory; watchdog handles inspect creation time of owned children only.

Modes7/8/5 use the already compiled host_controls_v1 binary from MAIN commit
117a895b2ceb52cddcca12c233eeefc2badf0307. The CUDA source, ABI, independent CPU
builder, cubin and host binary were copied byte-for-byte, not optimized here.
The full reverse is CPU-built then transferred. No GPU builder or concurrent
preparation was implemented or run. The common RCC API GPU backend is not validated.

config/PLAN.json fixes smoke first, then one existing LJ input with q32 sources
in orders [7,8,5] and [5,8,7]. All q1/q2/q8/q32 prefixes and both orders are
reported, without selection or a success threshold. Direction/lean-Push q32
ratios were0.87576 and1.05441; Direction/equal-stop-Push ratios were0.93060 and
0.91188. The stronger lean control changes the winner. Do not average away
that disagreement or start extra runs to obtain a preferred answer.

Initial telemetry reported32 C+G contexts and two unreadable process names.
These remain unverified background. Other known research GPU names, foreign
pure-compute contexts/compute-engine activity, new PIDs, required telemetry
failure or sudden background3D changes would stop the session. This sampled
contract cannot prove absence of other CUDA work, full WSL coverage or enforced
exclusivity. Graphics, clocks, caches and host scheduling remain uncontrolled.

The new run consumed its one-session permission. No automatic retry, new input,
D0-D3 experiment, profiler, sanitizer, installation, paid resource or further
GPU query/execution followed completion. The remaining question is reliable
ready Direction utility against BOTH strengthened Push controls under a jointly
accepted measurement contract. The present result does not settle that question.

Raw per-request/per-worker outputs,201 distance arrays, commands,37 XML telemetry
snapshots, Windows engine records, watchdog states, release markers, hashes and
source pins are retained locally and in the result ZIP. Private Git contains
portable data/metadata derivatives with raw/public hash mappings; machine paths
are redacted and XML/binaries/full distance arrays remain in the ZIP.
