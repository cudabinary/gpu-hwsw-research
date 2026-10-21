# New fair-host GPU approval prerequisites and finite draft

Status: **NOT APPROVED, NOT DISPATCHABLE**. The new host has compiled and passed
CPU checks; the generic CPU transport is connected and OS-owned-child tested.
GPU PID/engine observation and CUDA retirement are not bound/validated in that
transport. The GPU CLI remains unavailable. Old broad permissions or old source
pins do not authorize this new executable.

## Exact code/review delta still needed

1. In a separate new adapter, bind the preserved exploratory NVIDIA PID/DXGI/
   engine/preflight guard at the existing parent observation cutpoints. Keep
   old strict code untouched. No protected/foreign process memory/module query,
   OS/security/driver/clock change or weakened stop condition is allowed.
2. Replace the CPU fixture-only process selector with a fresh, pinned new-owner
   selector under a new approval gate; allow only modes7/5, micro q3 and the
   fixed existing q32 sources. Pin new executable/source/header/config hashes
   and unchanged cubin/inputs. Require full C++ and Python distance validation,
   independent watchdog, PID/ACK and confirmed CUDA retirement for each worker.
3. Apply actual projected allocation expectations by mode (micro Push208,
   Direction312; LiveJournal Push275124, Direction501580) against actual owner
   allocation counters. Preserve common 32 MiB caps. Include owned monitor/
   watchdog memory in the host budget; CPU fixture coverage alone is insufficient.
   Keep unknown driver/OS physical usage explicit. Actual allocations must be
   measured/reported, not copied from projections.
4. Wire the new preparation fields, common full-output boundaries, required
   smoke/check overhead and mixed native setup into the ledger. No timestamp
   subtraction into pure host or allocation/H2D-only costs. Review the new
   guard binding with non-GPU child/failure fixtures before seeking execution.
   If safe binding needs a broad refactor, stop and report it.

No further owner/kernel change is currently required by source inspection.
If GPU correctness contradicts this, stop; do not patch kernels or retry
automatically under the same approval.

## First execution request after the binding is ready: F only

Question: does the unchanged cubin produce exact complete distances with the
new null-reverse Push path, while Direction and cancellation remain correct?

- Existing local RTX4060Ti, ISOLATION_UNVERIFIED.
- Fixed order: micro7 Push7 q3, then micro7 Direction5 q3; sources [0,1,4].
- Exactly at most **2 CUDA workers, 6 complete BFS arrays, 2 init-only cancels**.
- Whole dispatch <=120 seconds, each owned child watchdog20s. Warmups0/retries0.
- Application workspace cap32MiB; CPU Account cap32MiB; owned-host budget1GiB.
- Expected tiny application payloads above are projections; observed driver
  overhead is additional. Raw storage cap32MiB. No paid compute or new tools.
- Start free VRAM>=2048MiB, run free>=1536MiB, observed temp<78C, observation
  age<=3000ms, management timeout2s; required PID/engine/context checks intact.
- Stop on any CUDA/correctness/OOM/watchdog/deadline/budget/coverage failure,
  observable foreign research compute, abrupt observed environment change or
  unconfirmed own CUDA retirement. No second worker after a failed first one.

F is a correctness/instrumentation pilot, not timing success. No F run occurred.

## Separate later boundary/performance request, not included in F

Only after F and a new approval: four [7,5,5,7] target arms, each with its same
mandatory micro7 mode7/mode5 checks before one q32 target. Maximum12 CUDA workers,
152 complete BFS arrays, 8 init-only cancels; serial execution; total wall<=600s,
arm<=90s, child20s, three60s no-dispatch rests, <=480 management samples, raw<=128MiB.
The corrected mode-specific prep/allocation costs are charged. Actual graph
load, preparation, transfer, full-return, checks and retirement are retained.

This would measure a corrected pinned software baseline, not a public strongest
GPU BFS claim or HW need. No automatic D0-D3, Nsight, sanitizer, tuning, new
input, installation, cloud resource or final MAIN direction change is included.
