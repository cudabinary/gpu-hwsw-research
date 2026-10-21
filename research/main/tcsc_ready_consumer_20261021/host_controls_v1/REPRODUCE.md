# Reproduce CPU/static preparation without GPU access

Use the existing Windows Python, WSL Ubuntu MinGW compiler and CUDA13.3 headers.
No installation or GPU management query is needed. Keep the version directory
beside the frozen round source so relative provenance references resolve.
Preserve existing outputs. For reproduction, use a fresh isolated copy excluding
generated owner/build/audit outputs and containing the same frozen parent inputs.

```text
python host_controls_v1/tools/prepare_sources.py
python host_controls_v1/tools/compile_static.py
python host_controls_v1/tools/run_targeted_cpu.py
```

The scripts refuse existing successful preparation/compile/test receipt paths.
Do not delete original results to rerun them. Compilation has a180-second cap;
the targeted CPU run has a30-second cap and the no-permit rejection a15-second cap.
The test wrapper removes every TCSC execution variable from its child environment.
It does not set either the old or new execution permit. Do not use an old GPU
permit or run the GPU dispatcher as part of this reproduction.

The generated owner uses src/host_controls.hpp for both the host traversal
decisions and its CPU replay. src/targeted_tests.inc checks eight specific cases
against the frozen independent queue oracle, plus invalid variants and metadata
boundaries. All raw test lines and the pre-driver rejection are under audit/.
Those checks are not a GPU implementation/runtime proof or sanitizer result.

config/PINS.json records source/binary/input identities. SHA256SUMS covers this
version's code, settings, documentation and raw local results. The copied cubin
and builder remain byte-identical to the parent. The old owner, old executable,
old source pins, old reports and old 402-array receipt remain unchanged.

Git publication may replace machine-specific compiler paths with VERSION_ROOT.
The private local raw compile receipt remains preserved; PUBLICATION_MAP.json
in the parent Git checkpoint distinguishes raw versus published hashes.
