# Source and bridge reconciliation

## Strongest-baseline audit

Original OLD_P2 is a valid non-RCC baseline. With the original LiveJournal input and a resident consumer, OLD_P2 took 0.7263 times as long as PUSH_N. The median paired DO_RIE / OLD_P2 ratio was **1.0505**. RIE reduced work relative to DO_N within the same adapter. Runtime also depends on exact discovery counting, termination checks, the bridge's validation and control logic, and code generation. The experiment did not isolate those individual contributions.

The initial service gate omitted OLD_P0 and OLD_P2. The configuration in `config/service_modes.txt` and the original aggregation were preserved. `CPU_INCREMENTAL_VALUE.csv` was regenerated from existing raw data to include these modes in the strongest resident baseline. The initial aggregation is retained in `results/INITIAL_GATE_INCREMENTAL_SUMMARY.csv`. No additional CPU benchmark was run at this checkpoint.

In the measured cold q32 service, Push+RCC_TABLE took 0.7999 times as long as PUSH_N and 0.8999 times as long as sequential DO_RIE. **The strongest full-service path remains unknown at this checkpoint**, pending a comparison with original OLD_P2 under the same owned-output contract. The earlier P2 value of 0.840713 used a different measurement boundary. The minimum follow-up is a paired comparison of frozen P2's sequential and ready paths against Push+RCC_TABLE under the same output contract. It was outside this checkpoint's completed budget of three CPU processes with seven rounds each.

The GPU pilot checked correctness for two candidates and their controls. It passed cancellation, source switching, and full-array comparisons. Graph version mismatch, allocation failure, and dispatch limits were covered through CPU tests or static guards. The pilot did not inject those failures on the GPU or measure the missing CPU baseline.

After the external download failed, the study used a local attachment with the same name and size. The 7,431,945-byte ZIP had SHA-256 `b2c6f4d49d0af97e11125c1588e444f85e6255ecf1b54a165ba4920d004b963b`. CRC, path traversal, duplicate name, and link checks passed. The 73-file outer manifest and the nested ZIP manifests were rechecked. `audit/INPUT_FREEZE.json` records the hashes and check counts for each nested ZIP.

The three vendored consumer sources match the local originals byte for byte. The original 197-file manifest and 22 benchmark pins were rechecked at completion. Earlier Consumer-first ratios on LiveJournal q32 were 0.840713 sequential and 0.865155 concurrent. Those results retain their own scope, with different PUSH_N, owned-output, and certificate-publication assumptions from the new study.

The comparison checked 26,730 fields across nine common modes and 18 graph and schedule combinations against historical bridge records. There were zero mismatches. The new full arrays validated in Python also matched 864 historical exports. The 87,552 historical cases came from prior C++ runs and are reported separately from the new checks.

Limits and contractual differences:

- The bridge Push field `levels=0` means uninstrumented. New Push counts expanded rows and levels.
- The original bridge LAST returned a scratch or buffer reference valid until the next call. The new module pays to return an independently owned complete array.
- The bridge cache lacked budget and allocation-failure fallback. The new adapter adds them.
- Original RCC Direction uses a different definition of `remaining` from Codex's exact indegree sum. Treat their timings as distinct backends.
- The original and holdout schedules had already been seen. One new order was fixed in advance with seed `20261021`.
- Relabeling the original schedule follows the vertex map. A numeric source in the holdout need not name the corresponding relabeled vertex.
- The supplied EPYC/g++ 14.2 timings and the new i5-14500/WSL/g++ 15.2 timings come from different environments.

The initial ZIP reader paused while looking for duplicate README names after the import and CRC checks had completed. The three required documents were read in order using their exact paths. This tooling issue is outside the experiment's success and failure counts.
