# CPU reproduction

## Check package integrity

```bash
python3 tools/verify_package.py
```

## Rebuild and verify

Use installed g++ and Python. Build your own executables from the included source.

```bash
make all
./build/scope_probe test
./build/distance_probe test
```

- Scope covers 4,736 graph configurations and 416,768 mode-query comparisons.
- DistanceGuard covers 640 graph configurations and 51,200 mode-query comparisons.
- The suites partially overlap and include exhaustive tiny graphs and comparisons with existing baselines.
- GPU and sanitizer checks were outside the package's scope.

## Independently verify saved outputs

```bash
python3 tools/verify_guards.py
```

This recomputes Python deque BFS from raw `.edges`, checks 768 saved guard arrays, and verifies counterexamples and inequalities.

To verify Scope arrays and reaggregate CSVs, use an environment with pandas installed.

```bash
python3 tools/verify_and_analyze.py
python3 tools/analyze_guard.py
```

The commands rewrite derived summaries. Keep the original ZIP and use a separate extracted copy. Rewritten files may differ from the original manifest.

## Generate fresh CPU diagnostic outputs

```bash
mkdir -p replay
./build/scope_probe diagnose fixtures replay
./build/distance_probe diagnose fixtures replay
```

Output writes and verification are outside performance timing. Use a fresh output directory to preserve the historical diagnostics.

## Run a fresh CPU measurement

Each command runs one foreground CPU process. Create `replay/` first.

```bash
mkdir -p replay
./build/scope_probe bench fixtures 0 > replay/scope_session0.csv
./build/scope_probe cold fixtures 0 > replay/scope_cold_session0.csv
./build/distance_probe bench fixtures 0 > replay/guard_session0.csv
```

Only sessions 0, 1, and 2 are accepted. The fixed round counts are seven for Scope resident, three for Scope cold, and seven for Guard resident. Compare within the same machine and experiment. `PROTOCOL_FROZEN.json` and `GUARD_PROTOCOL_FROZEN.json` record the request bounds.

`bench` assumes a resident reverse index and includes certificate-cache and workspace preparation, maintenance, output copying, and release. `cold` assumes resident CSR and includes construction and internal validation of the reference reverse index when needed. Parsing and input loading are outside both measurements. DistanceGuard was measured with resident reverse only.

## Limits

Scratch and cache counts measure array payload. Account separately for allocator and process memory and for retained snapshots held by external readers. The executor API has one owner. Concurrent CPU or CUDA execution and new sanitizer runs were outside the package's scope.
