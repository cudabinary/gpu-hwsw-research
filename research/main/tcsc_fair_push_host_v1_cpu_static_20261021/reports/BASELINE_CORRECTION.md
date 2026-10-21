# What changed and what is charged

## Exact Push information without reverse adjacency

The retained Push7 termination is B(s)=K+[indegree(s)==0], where K is the
number of vertices with positive indegree. Every reachable non-source vertex
has an incoming edge. Once B(s) distinct vertices have been discovered, no
undiscovered reachable vertex remains. Unreachable positive-indegree components
can prevent this certificate from firing; the ordinary empty-frontier exit
still returns exact distances. Successful unique discoveries, not attempted
edges, must be counted; the existing kernel's atomicCAS/append logic is unchanged.

`fair_preparation.hpp` computes this information directly from immutable CSR:
zero a ceil(n/64)-word bitset, scan every CSR destination, set its bit and count
first occurrences. It retains the bitset and K so any single source can be
checked in O(1). Duplicates and self loops do not inflate K. This is small exact
sufficient metadata, not a claim of global time/space optimality or novelty.

For n=4096, m=48292, it pays 64 zeroed words, 48292 logical destination/bitmap
tests and 512 bytes of retained bitmap payload, plus normal object/allocator
overhead. The CPU time includes allocation, zeroing, scanning and publication.
It is not free indegree knowledge, a full indegree-count histogram or partial
reverse index. Logical operations/bytes are not measured DRAM traffic.

The metadata holds a strong immutable graph reference, checks identity/version,
and is exposed only after complete construction. Missing/stale metadata uses
the exact EARLY_N bound; invalid source is rejected. Allocation failure and
pre-cancellation throw before a GPU path is reached; no partial object is
published. Tests cover allocation rollback, pre-cancel, duplicate/self-loop
semantics and lifetime ownership. Mid-kernel cancellation is not tested here.

## Necessary preparation by path

| Work/state | Push7 | Direction5 |
|---|---|---|
| CSR load/storage | Required and charged | Required and charged |
| Indegree-presence bitmap/K on CPU | Required and charged | Not built; unused static metadata removed |
| Full reverse COUNT/scan/cursor/scatter/verify | Absent | Existing builder, fully charged |
| Reverse device allocation/H2D | Absent | Required and charged |
| Device bitmap | Absent | Required for existing Direction kernels |
| Frontier/distance/counter/error state | Required and charged | Required and charged |
| CPU oracle/replay and full output checks | Retained | Retained |

Direction's unused old IncomingBound construction is also removed; there is
no reason to penalize it with Push-specific metadata. The shared stop helper,
Direction policy/thresholds and complete reverse builder remain byte-identical.
The new owner deliberately supports only the compared modes 5 and 7.

The old owner required reverse even for Push and unconditionally built it.
That remains true of the preserved binary, but **not** the new host variant.
The corrected execution path exists; it is not a timer subtraction or modeled
counterfactual. CPU oracle/replay for Push also avoids building a hidden reverse.

## Accounting and timing boundaries

Algorithm fields are `algorithm_preparation_ms`, `cpu_static_bound_ms` and
`cpu_reverse_build_ms`, recorded before the separate CPU oracle/replay timer.
The old in-Owner `static_bound_setup_ms` is now zero; metadata is already
prepared and charged before the native setup region. New CPU metadata timing
must not be mislabeled as inside the old native setup timer.

Both paths use identical graph/source/full-distance-output contracts. The
ready-consumer boundary still includes query initialization, events, level
synchronization, safety checks, complete D2H and owned publication. Native
context/ACK/allocation/H2D remain one mixed setup region. The wrapper cannot
split allocation-only/H2D-only time from its observations, so those remain
UNKNOWN. Cold must include setup and required experimental checks as separately
labeled components; do not omit either or subtract checks into a fictional
production latency. Nested intervals are not summed, and host-event differences
are not pure host time. External q1/q2/q8 completion is still unsupported by
the q32 buffered-return owner.

## Memory: common caps, different actual payloads

| Fixed LiveJournal input | Push7 | Direction5 | Evidence type |
|---|---:|---:|---|
| CPU preparation final bytes | 512 | 225944 | Actual Account counter |
| CPU preparation peak bytes | 512 | 291480 | Actual Account counter |
| CPU preparation allocation calls | 1 | 4 | Actual Account counter |
| Device application allocation sum | 275124 | 501580 | Static projection, no GPU allocation |
| CSR/reverse logical H2D bytes | 225944 | 451888 | Source-derived, not transfer timing |

Push eliminates 226456 projected device bytes: 225944 reverse bytes and 512
device-bitmap bytes. It eliminates 225944 logical reverse H2D bytes. Its 512-byte
CPU metadata remains charged. Direction's builder temporary buffers remain in
the CPU Account peak. Original CSR, final states and workspace are all counted.
The two one-shot CPU preparation timer samples are preserved in CSV/logs, but
are not a benchmark campaign or GPU-throughput prediction.

Both retain 32 MiB application-device and CPU-preparation Account caps and the
proposed 1 GiB owned-host-group budget. The CPU process adapter reads only owned
coordinator/fixture/watchdog handles. Summed per-process peak private commit is
a conservative group bound, not simultaneous physical memory. CPU observed
values, projected GPU requests and UNKNOWN driver/OS shared memory are separate.
No equal actual footprint, full physical peak coverage or GPU memory safety is
claimed. The GPU monitor helper's memory is not validated by CPU fixture tests.

## Static CUDA contract, still unexecuted

View stays 112 bytes and Counter 24 bytes; original kernel source/cubin hashes
are unchanged. New Push sets reverse row/source/bitmap pointers to null, passes
stats=0 to r_push and never selects r_mark/r_pull. The unchanged r_init does not
read reverse state, and append's reverse-degree access is guarded by stats.
This is source/ABI reasoning plus host compilation, not GPU validation. A new
correctness pilot must confirm null-reverse execution before timing claims.
