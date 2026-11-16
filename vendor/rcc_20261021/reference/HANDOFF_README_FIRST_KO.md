# Research handoff — validated Direction traversal and exact termination

Start with [the original work order](HANDOFF_CODEX_WORK_ORDER_KO.txt) and [the integration review](HANDOFF_MERGE_REVIEW_KO.md).

The latest Codex result confirmed an end-to-end cold CPU improvement on LJ4096 at q32. The earlier TCSC results applied to a different version. Sequential preparation remained faster than concurrent preparation, and preparation still had a cost. GPU and hardware contributions remained unestablished.

The independent probe used the sum of indegrees of undiscovered vertices, a statistic Codex already maintains, as a stopping condition (RIE). On LiveJournal, RCC skipped no further work after RIE. RCC supplied additional information in synthetic cases with disconnected reachable regions. Compare traversal algorithms and stopping certificates independently.

## Original package contents

- `original_archives/` held byte-for-byte copies of the two original ZIPs supplied for the Codex and RCC projects.
- `source_reports/` held reading copies of the original reports.
- `independent_bridge/` contained the independently implemented and executed C++ termination adapter, original vendored Codex source, inputs, checks, raw timings, and work counts.
- `evidence/` contained CRC and SHA results, equivalence checks on the five shared inputs, reaggregated Codex CSVs, and independent build and test logs.
- `ROLE_SPLIT_AND_NEXT_MERGE.md` described the independent Codex and ChatGPT research roles.
- `tools/verify_delivery.py` checked package hashes without using the GPU or uploading data.
- `tools/unpack_sources.py` extracted the original ZIPs into an empty `sources` directory without running code or downloading files.

## Historical execution scope

The work order covered CPU analysis, implementation, and static compilation. GPU queries and execution, Nsight, sanitizers, installations, external transfers, and paid resources were outside its scope. The earlier 9,692-BFS GPU proposal remained disabled.

The handoff paired the local ZIP with `CODEX_WORK_ORDER_KO.txt`. When an original already existed in the Codex project, it was checked by hash and read in place. Preserve original and unrelated workspaces.
