# Reproduction

Existing tools only: WSL Ubuntu, mingw-w64 g++13-posix, CUDA13.3 driver headers,
Windows Python3 and bundled PowerShell. No packages were installed.

1. Preserve the package and verify SHA256SUMS.
2. CPU/static: `python3 tools/adapt_owner.py`, then under WSL
   `python3 tools/build_native.py`. Use existing source headers and toolchain.
3. Native Windows: `python tools/cpu_preflight.py` (18 positive cases / 402
   complete arrays, four negative arguments, no CUDA driver initialization).
4. `python tools/test_watchdog.py` tests only disposable owned CPU children.
5. `python tools/adapt_dispatch.py` regenerates the bounded dispatcher from the
   preserved historical script. `python tools/prepare_plan.py` freezes the
   comparison before performance. Preserve all attempt outputs separately.
6. GPU is currently blocked. Do not replay `run_one_session.py` in this directory:
   it deliberately refuses to overwrite the failed session. Resolve the human
   lock/session prerequisite without changing safety rules, use a new capture
   location and fresh identity baseline, then pin all runtime files before CUDA.

The package includes selected unchanged safety sources/binaries copied from the
authenticated archive, not the large private recovery manifests. For full archive
recovery use GitHub evidence/archive/20261021 and its private B2 locator; GitHub
access is not B2 authorization. Keys are never included. Original source paths
are not assumed to exist after the approved archive cleanup.

Owned distances, once a future GPU run succeeds, are captured after the timed
batch as q*n little-endian int32 values. Validate them independently with the
same input and sources before accepting timing. q1/2/8/32 are prefix timestamps
of the same batch, not four independent or online arrival experiments.
