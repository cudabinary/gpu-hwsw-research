# Reproduce evidence analysis; do not automatically repeat GPU dispatch

The results are from one consumed exploratory session. GPU reproducibility is
not permission to run another session. Existing strict mode and its old blocked
result remain preserved at the parent MAIN round.

## Inspect without GPU access

Verify config/PLAN.json against audit/PLAN_SHA256.txt and every pinned input,
source, helper and binary. Verify SHA256SUMS for all saved result members.
results/EXPLORATORY_SESSION/RECEIPT.json identifies all nine completed cases;
each command/stdout/stderr/full distances file and watchdog receipt is retained.
STRICT_PRESERVATION_CHECK.json and POSTSESSION_PIN_CHECK.json record preservation.

The C++ owner checks full distances using its independent queue oracle and
replay trajectory. The Python runner independently compares the raw little-
endian int32 outputs with a queue BFS for the fixed sources. Each GPU array is
counted once despite two checks. Init-only cancellation is a separate query
and does not publish an output. It does not test mid-kernel preemption.

In a fresh local copy excluding results/analysis, regenerate only analysis:

```text
python tools/analyze_results.py
```

The script reads existing files, refuses an existing analysis directory, and
does not load or query CUDA. Do not delete original evidence to reproduce it.
CPU preparation times, native setup, owned-output prefixes, event intervals and
worker windows have separate fields; never treat them as one pure GPU duration.

## Source/build provenance

The owner source/binary and unchanged kernels/cubin are exact copies of
host_controls_v1 from MAIN commit117a895b2ceb52cddcca12c233eeefc2badf0307.
The previous targeted CPU/static receipts are included as prior evidence and
were not rerun or recounted as GPU validation. No new compilation was needed.
The current runner, plan and input hashes were frozen before the first device
query. A Python syntax error was corrected in preparation before any GPU query;
the draft and final preexecution receipts are preserved, not execution results.

The installed native NVIDIA management tool and Windows GPU Engine counters
provided sampled observations. DXGI only mapped the NVIDIA adapter LUID. No
protected-process module/memory query, new security permission, driver setting
or installation was used. The independent watchdog applies only to the owned
child PID plus creation time. Previous exact watchdog tests are retained.

## Future execution requires new coordination

tools/run_exploratory.py requires the explicit exploratory flag, immutable pins
and a fresh nonexistent result directory. It refuses this consumed directory.
Its source records the exact command shape, child-only execution permits,
watchdog20s, session600s and resource limits. The two permits are cleared from
the inherited environment before fresh child values are supplied by that run.
Do not rename output directories, set flags manually or reuse this permission
to repeat the campaign. Review the next finite contract first.

The full raw ZIP is private user evidence. The Git publication omits raw XML,
executable/cubin and binary distance files, strips personal machine paths from
published JSON, and supplies PUBLICATION_MAP.json with raw/published hashes.
SHA256SUMS in the private ZIP applies to raw bytes. Published checksums apply
to the portable Git derivatives. Credentials are not included in either.
