# Reproduce only the CPU arithmetic follow-up

Keep the original experiment files read-only. In a new copy of this follow-up
directory without calculations/, retain the same parent results/source/plan:

```text
python analyze_existing_records.py
python write_metadata.py
```

The scripts use only Python standard-library file reads/arithmetic. No
subprocess, GPU API, BFS execution, performance benchmark, compiler, sanitizer,
installation or remote request is part of the calculations. Existing output
directories are refused rather than overwritten. No prior402-case suite is run.

Input SHA-256 values are in calculations/SUMMARY.json. Exact source timing
anchors are in TIMING_BOUNDARIES.json. Source logs supply192 timing requests;
the saved smoke evidence is not used as timing replication. q-prefixes are
nested;32 sources are not32 repetitions of the same request. No confidence
interval or statistical independence is asserted.

The old result ZIP and strict/HOLD evidence remain unchanged. GPU_APPROVAL_REQUEST
is a document only, and PROPOSED_GPU_PLAN.json has dispatch_ready=false and
execution_authorized=false. Do not execute any GPU runner to reproduce this
analysis. Raw records and required full distance arrays remain in the existing
private Library result ZIP and original local experiment folder.
