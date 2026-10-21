# Fair Push preparation: separate host revision, CPU/static only

The baseline defect is corrected in **a new host source and binary**. Lean
Push7 now prepares only exact CSR indegree-presence metadata; it builds,
allocates and transfers no reverse adjacency or device bitmap. Direction5
still pays the unchanged complete reverse builder and all required device
state. Original binaries/sources, kernel source/cubin/ABI, strict guards,
RCC and historical results are preserved.

This round performed **zero GPU queries or dispatches**, zero new CUDA kernel
compilations, zero installs and zero paid compute. One new Windows host static
compile/link passed with existing MinGW/CUDA headers. New GPU correctness,
timing, driver memory, engine/PID observations and CUDA retirement remain
UNKNOWN. The default wrapper GPU route remains unbound/disabled.

## Delivered evidence

- 534 bounded CPU graphs: 3294 complete Push/Direction distance-array checks,
  1647 new-versus-old bound comparisons, 10 negative/lifetime checks PASS.
- 70 compiled CPU fixture arrays PASS; independent Python checks those same
  70 arrays (not 70 additional unique requests).
- Final 24 mock scenarios PASS. Earlier mock outputs are retained and are not
  pooled as additional independent tests.
- Real owned CPU process transport: 9 checks PASS, plus 3 targeted coordinator
  stop/cleanup checks. Total CPU protocol fixtures/watchdogs including the
  single preliminary check: 23 of each. These children never load CUDA and
  their protocol payloads are not BFS arrays.
- Four saved real CPU owner reports bound to the wrapper schema; 8 deliberately
  invalid preparation/output cases rejected.

On the fixed LiveJournal derivative, CPU preparation Account live/peak bytes
are Push **512/512** and Direction **225944/291480**. Static device allocation
sums are **275124** and **501580** bytes. These sums are not GPU-measured peaks.
Common allocation limits are unchanged; actual requirements are intentionally
different. OS/driver shared physical usage is not claimed equal.

Read `reports/BASELINE_CORRECTION.md`, `reports/VALIDATION_AND_LIMITS.md` and
`GPU_PILOT_APPROVAL_REQUEST.md`. Reproduction commands and hash provenance are
in `REPRODUCE.md`. All raw logs, source, binary, unchanged cubin, fixtures,
mock/CPU protocol records and hash lists are included in the private delivery.
Private Git contains sanitized text and raw hash links, not binary arrays.

This is a baseline correction, not a new BFS algorithm, new GPU mechanism,
performance success or hardware-necessity result. Do not combine this host
revision's future times with S1/S2/S3 as if the binaries were identical.
