# Ready-consumer attribution verdict

**A positive mode5/mode0 result cannot establish a contribution from our
preparation method. The internal Push also lacks a cheaper static equivalent
of the RIE stop. Keep HOLD_ENVIRONMENT; no GPU observation was repeated.**

Reuse `reports/IMPLEMENTATION_AND_CONTRACT.md` and
`reports/PREREGISTERED_PROTOCOL.md` for the existing boundary and limitations.
This note adds the missing code comparison and bounded operation accounting.
It does not repeat the 402-array correctness suite or WFA audit, change the
consumer/builder, or estimate GPU time from CPU work.

## What differs in the actual executable paths?

| Aspect | Pinned code location | Attribution consequence |
|---|---|---|
| Internal Push | `src/kernels.cu:18-24`; `src/owner.cpp:82` | Same one-thread-per-frontier-row kernel for modes0/6, serial row loop. This is not a demonstrated best public load-balanced GPU BFS. |
| Stop conditions | `src/owner.cpp:69-76` | All use EARLY_N; modes4/5 add frontier-zero, modes3/5 add RIE, zero first. A 5/0 comparison bundles these with Direction. |
| Policy maintenance | `src/kernels.cu:13-17`; `src/owner.cpp:60-61,86` | Every newly discovered vertex in modes2-6 adds two 64-bit degree atomics and four degree-offset loads. Mode0 does not. RIE-disabled modes still maintain indegree statistics for policy. |
| Mode6 control | `src/owner.cpp:75-82`; compare `include/consumers.cpp:16-19` | GPU mode6 skips switching and bitmap work entirely. It isolates degree maintenance, not full shadow-policy cost. CPU Stats-Push retains the shadow bitmap; its name does not imply identical GPU control. |
| Frontier / pull | `src/owner.cpp:42,79-87`; `src/kernels.cu:9-12,25-30` | Shared dense frontier queues. Pull adds bitmap clear/mark, scans vertex IDs, and early-exits incoming lists; this is ordinary Direction traversal. No partial index is consumed. |
| Initialization / allocation | `src/owner.cpp:34-48,57-63,92` | All six modes allocate the same CSR/reverse/bitmap/workspace outside the batch. Each query initializes n distances, creates/destroys events and allocates an n-element owned host result inside timing. Equal ready-state allocation is not a no-preparation service comparison. |
| Synchronization / safety | `src/owner.cpp:74,83-89`; `src/native_driver.hpp:48,53` | Each processed level clears 24 counter bytes, synchronizes, copies 24+4 control bytes, and queries free memory. Removing a level removes host/control/safety work too; do not label all saved time a GPU traversal or memory effect. Guards remain enabled. |
| Return boundary / first use | `src/owner.cpp:89-94,140-148`; `src/native_driver.hpp:35-37` | Query and q-prefix include full distance D2H and owned publication. Validation/file/log output follows the batch. The event interval contains host submission gaps, not just kernel busy time. First-use kernel-handle lookup remains inside queries; warmup is zero. |

CPU reverse construction, input transfer and context setup precede the batch
(`src/owner.cpp:129-140`). There is no GPU builder, publication overlap or Plan-A
concurrency measurement. A ready-state win cannot establish construction,
reuse-service or HW advantage, even with perfect measurement isolation.

## A static identity that already removes RIE's stopping work

Let `K` be the number of vertices with positive indegree and
`B(s) = K + [indegree(s)==0]`. Every reached vertex other than the source has
positive indegree. Therefore, for this exact complete-distance BFS contract:

`remaining_in == 0` **iff** `seen == B(s)`.

Both directions follow because remaining_in sums nonnegative indegrees over
unreached vertices. Duplicates and self-loops do not invalidate the identity.
This is an elementary static counting bound, not RCC development, an oracle,
a novel algorithm or a newly implemented consumer. It says nothing about
general reachability beyond this upper bound.

With the already prepared reverse, compute K once from n row-offset differences,
store one graph-versioned scalar, and test the source's indegree once. Push can
then use the existing seen count without per-discovery degree atomics for this
certificate. Without ready indegrees, construction/COUNT and storage are real
costs and must be charged. Direction still needs remaining_in for its current
switching threshold; the identity does not remove that policy cost.

LJ has K=4095 of 4096; Google K=1024 of 1024. Thus Google's RIE condition is exactly
EARLY_N. Source0 in LJ also has the original n bound. The frontier-zero guard
can remove other empty tails; it requires an outgoing-frontier statistic and
is not free to an otherwise lean Push. For Direction it uses a maintained value.

## Raw work accounting, q32

Each cell is **logical edge tests / processed levels / derived kernel launches**.
These are deterministic accounting of fixed inputs, not measured GPU operations
or time. Hypothetical Push controls are projections from saved traces, not code.

| Path | LJ4096 | Google1024 |
|---|---:|---:|
| Existing Push0 | 1,455,871 /199 /231 | 134,898 /266 /298 |
| Existing Direction4 + zero | 811,669 /198 /344 | 265,846 /257 /428 |
| Existing Direction5 + zero + RIE | 810,522 /168 /289 | 265,846 /257 /428 |
| Projected lean Push + B(s) | 1,191,634 /169 /201 | 134,898 /266 /298 |
| Projected stats-Push + B(s) + zero | 1,191,634 /168 /200 | 134,898 /257 /289 |

In LJ, RIE after zero removes 1,147 edge tests, 30 level synchronizations and
55 launches, including mark kernels; a large time change could therefore be
mostly control/empty-work savings. B(s) supplies exactly the same certificate.
Direction5 still tests fewer edges than either strengthened Push projection,
but launches 89 more kernels than the equal-stop stats-Push and performs
253,830 degree atomics, 88,760 bitmap atomic ORs and 364,544 distance probes.
These counts cannot decide elapsed time or SM/L2/DRAM causality. Google tests
more edges with Direction and gets no extra stopping work from RIE.

All paths initialize and return the same full distances. Device payload is
501,580 bytes for LJ and 82,380 for Google in the current ready-state owner.
Raw q1/2/8/32, query and level counts, pins and limits accompany this note.

## Smallest useful follow-up, frozen as a proposal only

Keep existing modes0/6/4/5 and add **host-only controls**, not new kernels:
lean Push+B(s), and stats-Push+B(s)+zero. The latter shares mode5's stopping
levels and statistics while executing Push; the former prevents treating an
intentionally expensive statistics control as the strongest practical Push.
Compare 6/0 (maintenance), bound-Push/0 (static certificate), 5/4 (incremental
RIE after zero), and5/both strengthened Push controls (ready Direction utility).
Report all predeclared paths; no threshold/input search or adaptive new control.

This replaces redundant modes2/3 in a **future reviewed protocol**, not the
current pinned plan. Same two inputs, q32 sources, alpha15/beta24, three fixed
paired blocks, q1/2/8/32 prefixes and six micro gates can fit the former ceilings:
42 workers,1170 BFS arrays,6 init-only cancellations. No existing guard, permit
or source/binary pin is changed. The two controls are not implemented; a small
host adapter, new pins and functional checks are required before any dispatch.
No protected-process query, environment retry or GPU execution is requested now.

One open question: **Does ready Direction beat both the cheap static-bound Push
and the equal-stop Push at the same full-output boundary on this GPU?**

A 5/0 win alone is insufficient. A win over both strengthened controls would
establish utility of this existing Direction consumer, not our builder or new
HW. A loss stops preparation expansion for these inputs/contract, not all GPU
graphs. A positive edge-count result alone is insufficient in either direction.
The existing 0.95 exploratory gate is not a noninferiority/statistical claim;
if retained after review, require the comparison with both stronger controls
in every fixed block and publish all results. Preparation-inclusive service
remains a separate, unimplemented experiment.
