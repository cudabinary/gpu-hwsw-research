# CPU-only reproduction

The only computation is hashing and reaggregation of existing files. Do not
execute the captured C++ binary, CUDA cubin, or session-runner scripts.

For an extracted package with the input capsule present, use Python 3 and its
standard library:

```text
python tools/audit_sessions.py analyze --output reproduction
```

The output folder must be new; existing inputs/results are never replaced.
Compare the resulting CSV/JSON files with `calculations`. Byte equivalence,
normalized commands, reported counters/work and output-array hashes are
asserted. The process does not reconstruct an unmeasured timeline or rerun BFS.

The initial capture, performed once against existing sibling projects, was:

```text
python tools/audit_sessions.py capture
python tools/audit_sessions.py analyze
```

The capture's original workspace-relative source locations and SHA-256 are
in `INPUT_MANIFEST.json`; a different computer needs the included capsule or
an authenticated original-archive restore, not the old machine's absolute paths.
Raw JSON/logs may contain local paths. Git provides a redacted derivative;
its `PUBLICATION_MAP.json` distinguishes original and published hashes. A
sanitized derivative is not a byte-identical substitute for raw inputs.

The recorded environment overrides are read from Python AST, not executed.
Compiler flags are read from the original compile receipt, not inferred from
current tools. Clock/P-state values are parsed from preserved XML, never queried
again. All 90 snapshots lack per-query timeline alignment; missing historical
environment, clocks during kernels, cache state and isolation stay UNKNOWN.

All correspondences use fixed session/block/mode/source labels. Different
worker/smoke order and parent orchestration prevent treating them as exact
replications. Reused historical requests are not independent samples. No
confidence interval, statistical winner, GPU busy-time estimate or GPU-memory
traffic estimate is generated. Safety checks remain represented in the actual
historical timing boundary.
