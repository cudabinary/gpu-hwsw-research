# Research Evidence Index — 2026-10-21

The survey covered 110,593 file locations across 16 original research roots and preserved all 110,593. The archive contains verified byte versions of individual files. The running research projects were captured without pausing them for a single coordinated snapshot.

- 56,882 unique content items, totaling 51,673,113,320 bytes.
- 110,626 indexed locations, including 33 derived artifacts such as Git bundles and SQLite snapshots.
- All logical content passed SHA-256 verification after reconstruction from remote bytes. Representative files were also restored into a separate empty directory.
- `BACKED_UP_VERIFIED` records preservation integrity. Scientific validity, performance, and novelty depend on their own evidence.
- GitHub hosts the index, reader tools, and restore guide. The original paths and large artifacts are in the authenticated private B2 archive.

Find evidence IDs of the form `sha256:abcd…` in `shards/ab.jsonl`. The index retains all original locations for a given hash. The private restore manifest provides the actual paths.

PAPER SCOUT and PAPER WRITER should start with the [handoff](PAPER_WRITER_HANDOFF.md), [coverage and limitations](EVIDENCE_COVERAGE_REPORT.md), and [restore guide](BACKUP_AND_RESTORE.md).

The Git commit identifies the published version of this index. Earlier experiments retain their own source commits, with `UNKNOWN` where the source commit was never recorded.
