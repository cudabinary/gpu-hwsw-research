# Interpreting the result files

- `results/gate_*.csv` covers three CPU processes and seven rounds. The `ns` field measures the resident consumer batch through full distance delivery. `priming_ns` measures the three historical requests used to warm the certificate. `validation_ns` and `release_ns` are separate.
- `CPU_CERTIFICATE_HISTORY_COST.csv` adds the measured priming and current consumer times. This sum has a CPU consumer measurement boundary and excludes the GPU service's reverse-build and transfer costs.
- `results/work.csv` measures cold-certificate work with a separate instrumented template. The final incremental CSV records warm work as UNKNOWN.
- CPU `remaining` and GPU `remaining_in` measure the exact indegree sum only in the new Direction path. Zero in Push or legacy diagnostics means the field is unused or unmeasured.
- The new CPU certificate path returns the exact reachable count via `Output::count()`. The legacy P0/P2 path guarantees the complete distance array and uses zero as a sentinel for an unknown count. On a nonempty graph, a completed BFS reaches at least its source. No public API imports a legacy result as an RCC certificate.
- `rows` counts source rows expanded by the new Push path. Zero in Direction and legacy paths means that counter is unavailable. `levels` counts levels actually expanded by new Push and Direction paths. Legacy bridge Push uses zero as an unimplemented counter.
- `CPU_COLD_WARM_SERVICE.csv` uses a resident graph with a cold, deferred, concurrent, or previously prepared reverse index. The certificate starts with the current result of A. The ready state refers to reverse-index availability.
- `median_paired_ratio` takes the median of ratios paired by process and round. A win is a ratio strictly below 1. Win counts alone provide no significance test.
- `CPU_STRONG_SERVICE_COMPARISON.csv` selects the strongest measured non-RCC service candidate. Original P2 is missing from that comparison.
- `payload_upper_bytes` is a conservative bound on array payload. RSS records the worker process high-water mark, including preloaded fixtures and the oracle.
- GPU `stream_interval_ms` is an event interval and includes host submission and synchronization. `wall_ms` includes copying and TABLE publication. Independent oracle validation is reported separately.
- Raw GPU stdout includes first-request cost, cancellation checks between sources, and separate validation timing. Full q32 GPU service, repeated GPU performance, and Plan A interference within 1% remain UNKNOWN.
