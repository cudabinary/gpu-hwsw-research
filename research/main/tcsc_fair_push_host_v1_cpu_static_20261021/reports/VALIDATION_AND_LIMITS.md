# Validation scope and remaining unknowns

## Actual completed work

One MinGW C++17 -O2 -static host compile/link using the existing CUDA13.3 headers
passed. No CUDA kernel was recompiled. The new PE executable is
`ee0985a51bfbf36ffdf1da8a91f158e905bfad1f8d2a43fadec289bf9de8cf08`.
The unchanged cubin is
`7cea25e119f9e1abbc583cb423db03db5d84f67c1b0dc02cc7170d3ef6b12836`.

`--fair-tests` exhaustively covers all directed simple graphs with n<=3 and
four targeted cases including duplicates, unreachable SCCs, empty edges and a
65-vertex bitmap-word boundary. There are 534 graphs, 3294 complete distance
comparisons and 1647 CSR-bitmap/reverse-bound comparisons. Ten negative/lifetime
checks passed. This tests the new host metadata and replay, not a GPU scheduler.

Four compiled --cpu-check fixture runs add 70 complete arrays; independent
Python checks the same 70 arrays. They are not 140 unique requests. Thus the
C++ unit/fixture checks total 3364 arrays, with 70 independently rechecked in
Python. CPU paths report driver_loaded=false and GPU_launches=0. ABI output
still reports View112/Counter24. All raw commands/logs/output arrays are retained.

The final 24 synthetic wrapper scenarios passed. Intermediate copies are kept
after connecting the adapter and correcting the new cost schema; do not sum
repeated scenarios into independent evidence. Four saved real CPU-owner reports
were bound through `fair_report_adapter`; eight false-preparation/hash cases
were rejected. GPU event/native/H2D values are never invented for CPU reports.

The real owned-child suite passed nine checks, using 19 CPU protocol children
and 19 independent watchdogs. It covers successful coordinator integration,
post-exit peak counter availability, nonzero exit, watchdog kill, parent cancel,
wrong ready PID, wrong output hash, missing CPU release marker and a deliberately
tiny host-budget rejection. A targeted three-child follow-up verifies actual
cancel stops before a fourth dispatch and cleanup includes the failed worker.
A simulated unconfirmed exit must not be reported confirmed. One preliminary
CPU child makes total protocol children/watchdogs 23 each. No foreign process
memory/module inspection, privileges or security changes were used.

The nominal twelve-child coordinator run observed summed per-process peak
private-commit counters of 30167040-30674944 bytes for coordinator, owned CPU
fixture and watchdog. These are real CPU OS counters, not GPU allocation or
driver physical memory. Final peak reads were available for all twelve. The
fixed CPU fixture carries protocol slots, not BFS distance arrays. CPU fixture
tests use zero inter-arm gap; they do not validate the future GPU rest protocol.

## Implementation review changes preserved

The first adapter implementation's cleanup considered only successful workers.
Review corrected it to include every attempted owned worker's transport receipt,
so an unconfirmed failed-child exit cannot be marked confirmed. The targeted
stop check validates that revision; old raw results were not overwritten.
The wrapper cost schema was then updated to charge new Push metadata separately
from reverse time, and final mock checks reran in a fresh directory. This is
bounded CPU development, not GPU retries or performance tuning.

## Not validated

Zero new GPU queries/launches were made. CUDA correctness, null-reverse device
execution, stream timeline, GPU initialization/allocation/H2D times, whole-service
winner, stable performance, GPU PID/engine telemetry and CUDA context retirement
remain UNKNOWN. Neither CPU output equality nor a CPU process-release marker
certifies any of these. No sanitizer/Nsight/install/paid resource was used.

The default GPU route remains unbound and hard-disabled. The new owner also
requires a distinct fresh fair-host permit before native driver initialization;
none was supplied. The CPU transport is connected, but the retained NVIDIA
engine/PID guard still requires a limited live adapter binding/review before
any separately approved GPU pilot. The old strict guard is unchanged.

No RCC development, original result rewrite, source deletion or final research
direction change occurred. This repairs a cost baseline; it does not establish
new algorithmic novelty, speedup, preparation overlap or hardware necessity.
