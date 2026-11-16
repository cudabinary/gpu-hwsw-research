# RCC-Scope and DistanceGuard CPU research package

This package implements and validates two CPU prototypes independently of the ongoing Consumer-first and RCC/RIE integration. The study used the local CPU and performed no remote-machine, GPU, Nsight, sanitizer, installation, or upload work.

## Results and design

- [Independent results](docs/INDEPENDENT_RESULTS_KO.md) records gains, losses, and timing boundaries.
- [Design and proofs](docs/DESIGN_PROOF_KO.md) covers stopping certificates and spatial or temporal candidate exclusion.
- [Prior work](docs/PRIOR_WORK_KO.md) covers related mechanisms and the open novelty question.
- [Logical read ledger](results/GUARD_LOGICAL_READ_LEDGER.csv) counts additional old-distance reads and avoided neighbor checks.
- [Validation summary](results/VALIDATION_SUMMARY.json) reports the executed tests.

## Implementation

- `include/closure_scope.hpp` restricts Pull candidates to a previously completed reachable set. It supports exact regional indegree, bounded certificate publication, and compaction and WCC controls.
- `include/distance_guard.hpp` retains the previous completed distance array and skips incoming lists for destinations that cannot be discovered at the current level. It compares COUNT, CLOSURE, RADIUS, and FRONTIER_MAX.
- `src/scope_probe.cpp` and `src/distance_probe.cpp` provide correctness checks, diagnostics, bounded uninstrumented timing, and full output export.
- `include/stop_bridge.hpp` and `vendor/consumer/` are unchanged sources from the earlier handoff.

The guard reduced logical edge probes beyond RIE on the Google and LiveJournal derived inputs. Full-cost CPU speed gains against strong software were found only for certain synthetic inputs and request patterns. GPU performance, overall baseline leadership, hardware requirements, and academic priority remain open.

Follow [REPRODUCE.md](REPRODUCE.md) with an installed C++17 compiler and Python 3. Verification uses Python's standard library, with pandas needed only for raw CSV reaggregation. The commands require no installations, GPU calls, or network access. The prototypes are standalone candidates for same-input, same-backend comparison after the earlier integration work.
