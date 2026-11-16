# RCC and RIE consumer integration — CPU results and native GPU pilot

## Strongest-baseline audit

Original OLD_P2 is a valid non-RCC baseline. With the original LiveJournal input and a resident consumer, OLD_P2 took 0.7263 times as long as PUSH_N. The median paired DO_RIE / OLD_P2 ratio was **1.0505**. RIE reduced work relative to DO_N within the same adapter. Runtime also depends on exact discovery counting, termination checks, the bridge's validation and control logic, and code generation. The experiment did not isolate those individual contributions.

The initial service gate omitted OLD_P0 and OLD_P2. The configuration in `config/service_modes.txt` and the original aggregation were preserved. `CPU_INCREMENTAL_VALUE.csv` was regenerated from existing raw data to include these modes in the strongest resident baseline. The initial aggregation is retained in `results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv`. No additional CPU benchmark was run at this checkpoint.

In the measured cold q32 service, Push+RCC_TABLE took 0.7999 times as long as PUSH_N and 0.8999 times as long as sequential DO_RIE. **The strongest full-service path remains unknown at this checkpoint**, pending a comparison with original OLD_P2 under the same owned-output contract. The earlier P2 value of 0.840713 used a different measurement boundary. The minimum follow-up is a paired comparison of frozen P2's sequential and ready paths against Push+RCC_TABLE under the same output contract. It was outside this checkpoint's completed budget of three CPU processes with seven rounds each.

The GPU pilot checked correctness for two candidates and their controls. It passed cancellation, source switching, and full-array comparisons. Graph version mismatch, allocation failure, and dispatch limits were covered through CPU tests or static guards. The pilot did not inject those failures on the GPU or measure the missing CPU baseline.

The decision was **selective CONTINUE_SW**. Direction+RIE and Push+RCC without a reverse index performed well under different cost conditions. On LiveJournal, RCC skipped zero additional checks after RIE, so the combined path was kept out of the service. The study used the existing node, head, and link representation and builders. It added no partial index or hardware engine.

- The CPU tests passed 240,415 full-distance comparisons and 988,173 assertions. They included 576 small graphs and 15,147 fixture requests.
- Independent Python checks passed for 1,836 arrays and 4,915,788 elements. The analysis also checked 864 historical bridge arrays.
- The CPU campaign used a fixed three processes and seven rounds, yielding 19,278 resident rows and 4,305 service rows. Thresholds were fixed at alpha=15 and beta=24.
- On an RTX 4060 Ti, 12 processes passed 36 full-distance BFS runs and 12 cancellation checks in 14.91 seconds. Minimum observed free VRAM was 6,878 MiB and peak temperature was 44°C.
- The GPU pilot launched 232 kernels. Static PTX and cubin builds and native owner linking passed. Nsight and sanitizer runs totaled zero.

For the original LiveJournal input at q32, CPU service time including A, preparation, and result delivery was 0.7999 times Push+EARLY_N for Push+RCC_TABLE and 0.8941 times Push+EARLY_N for sequential reverse construction followed by Direction+RIE. A resident reverse index changes which options are available. Retain the preparation cost when comparing cold paths. The GPU pilot checked correctness. Repeated GPU speed, 1% interference, and the need for hardware remain open.

Start with [the implementation](MERGED_CONSUMER_IMPLEMENTATION.md), [correctness and lifetime](CERTIFICATE_CORRECTNESS_AND_LIFETIME.md), [baseline reconciliation](SOURCE_BASELINE_RECONCILIATION.md), [cost analysis](COST_AND_INTERFERENCE_ANALYSIS.md), and [the decision](FINAL_DECISION.md). The original bundle contains `CPU_INCREMENTAL_VALUE.csv`, `CPU_COLD_WARM_SERVICE.csv`, `CPU_STRONG_SERVICE_COMPARISON.csv`, and the raw `results/`. The ZIP was retained locally at this checkpoint.
