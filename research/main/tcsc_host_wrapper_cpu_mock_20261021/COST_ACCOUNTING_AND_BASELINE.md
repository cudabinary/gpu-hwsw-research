# Cost boundaries, preparation fairness and memory

## Implemented ledger boundaries

The coordinator records ARM_BEGIN, the common setup/check phase, both required
smoke workers, SMOKE_GATE_COMPLETE, the target worker, cleanup and ARM_COMPLETE.
Within a worker it requires POPEN_RETURN -> READY_OBSERVED -> ACK_WRITTEN ->
CHILD_EXIT_OBSERVED -> RETIREMENT_CONFIRMED -> OUTPUT_VALIDATED. Out-of-order
or missing markers stop the campaign. The `.ready` marker is never identified
as resident-CSR/reverse readiness. Markers are parent observations; their
locations are validated only in the mock, not in a live process adapter.

The cold arm contains both required smoke/cancel/validation costs and the
target's complete preparation/return/check path. Target and smoke envelopes
are explicitly separate. Each arm has its own identical required gate; none
is allocated after seeing a favorable result. Waiting between arms belongs
to the campaign wall, not a target latency or proof of cold caches.

The receipt keeps these separate categories:

| Category | Fields | Interpretation |
|---|---|---|
| Mandatory experiment/safety work | reference check, monitor/preflight, required smoke envelopes, target CPU oracle/replay, post-batch validation, cleanup | Included in operational cold; not algorithm-only preparation |
| Algorithm preparation | CPU reverse builder and static metadata timers, graph load in child metrics | Known child subregions; static metadata is inside mixed native setup |
| Native mixed setup | context_setup_transfer_ms | Context/module/ACK/allocation/metadata/H2D aggregate; cannot split from wrapper records |
| Ready internal consumption | owned_ready_prefix_ms, wall/event/output-allocation-copy fields | Setup excluded, initialization/synchronization/full owned return included |
| Full target/cold envelopes | parent target and arm host spans | Contain the above regions; do not add nested spans |

The implementation deliberately leaves H2D-only and allocation-only UNKNOWN.
No event subtraction is labelled pure host execution. CPU event-record overhead
and real monotonic-clock precision are not measured by a virtual-clock test.
The safety/check costs cannot simply be subtracted into a hypothetical production
latency because they may change scheduling/cache state. Both totals and labeled
components are preserved rather than presenting that subtraction as a measurement.

The fixed owner still writes all q32 arrays to the external file only after
batch validation. Warm q1/q2/q8 prefixes are internal ownership times, not
external online returns. Cold external q1/q2/q8 remains unsupported/UNKNOWN.

## Fair full-cost baseline is absent in the fixed binary

Direct source inspection of preserved `owner_controls_v1.cpp` shows:

- Lines 125-129: the CLI selects fixture/n/mode/q; no skip-reverse flag exists.
- Line 133: `Builder.finish()` and `take()` run unconditionally before the mode's
  GPU execution, including before the CPU-check branch at line 137.
- Lines 37-38: Owner requires a matching non-null reverse and prepares incoming
  static metadata from it.
- Lines 45-47: when that reverse exists, full reverse/bitmap allocation and H2D
  are performed; this is true for the fixed Push mode as well as Direction.

Thus this comparison contract has **no path that charges Push only its required
CSR/static-metadata preparation**. Calling another mode or subtracting the
reverse timer does not create such an execution path. This is a limitation of
the inspected unchanged owner, not a claim that no such baseline exists anywhere.

Ready-consumer and equal-prepared-state cold measurements can be recorded, but
even favorable cold numbers cannot establish a winner over a strongest practical
no-reverse Push baseline. A fair no-reverse variant would require a separately
reviewed host/owner binary or an independently verified existing implementation,
plus exact distance/static-termination and memory tests. It is outside the
instruction to preserve this binary and was not implemented. No new algorithm,
builder or GPU kernel is proposed here.

## Common caps are not equal physical peaks

The same plan applies 32 MiB device application allocation, 32 MiB CPU builder
Account and a proposed 1 GiB conservative owned-host-group budget to both modes.
Expected target device application payload is 501580 bytes, including original
CSR, complete reverse, frontiers, distance, counters/error and bitmap. The mock
tests rejection of reported values above each cap and rejection of unknown host
coverage; it does not measure or hard-limit an actual OS process.

Each record distinguishes requested application bytes, builder-account peak and
the proposed owned-host peak upper bound. Real OS peak and driver/OS shared
physical memory remain UNKNOWN. A sum of owned-process peaks would be a
conservative bound, not simultaneous physical memory. Global free VRAM cannot
attribute driver allocations or prove complete total-memory equality. No memory
fairness or GPU performance conclusion is derived from the synthetic values.
