# Backup and restore

`ROOT_RECOVERY_LOCATOR.json` records the ID and SHA-256 of the authenticated remote checkpoint. The original absolute paths and manifest are available only in the private B2 object. Use authenticated access and keep tokens out of URLs and shared download links.

DPAPI-protected secrets from the original PC are machine-specific. On a different machine, enter an authorized restricted read key at the secure prompt. Keep the two Python reader scripts together and substitute the locator and evidence ID values for the placeholders.

```text
python tools/restore_evidence.py --root-file-id <ID> --root-sha256 <SHA256> --evidence-id sha256:<FILE_SHA256> --destination <NEW_DIRECTORY> --prompt-key
```

Use `--all` in place of `--evidence-id …` to restore all locations. The deduplicated download size and the disk space needed to materialize all original paths differ. Full restoration needs about 122 GB plus working headroom, which the tool checks before starting. Restore to a new directory. Use a native POSIX filesystem for POSIX-only names or case collisions.

For application use, restore SQLite from the consistent snapshots specified in `SQLITE_APPLICATION_RESTORE_MAP.json` and leave the old WAL and SHM files detached. Raw byte restoration serves a separate purpose. Point-in-time consistency across multiple databases remains unverified. Keep restored absolute links disconnected from the original machine.

The archive used usage-based B2 billing. The October 21, 2026 price snapshot recorded $6.95 per TB per 30 days, with the first 10 GB free. At about 51.7 GB, the estimate was $0.29 per month before tax and exchange rates. Downloads beyond three times average monthly storage were priced at $0.01 per GB. The approved $5 budget was a spending limit. Daily account caps do not guarantee a monthly cap. This checkpoint provides no ongoing backup, billing monitor, or Git synchronization after the session.

For a new research generation, reuse the existing mapping from logical SHA-256 values to remote extents and append new content. The frozen-run tools can resume the same manifest after an interruption. Repacking every file for each generation would duplicate storage. Preserve each new experiment's code pin alongside its manifest.

[Backblaze B2 pricing](https://www.backblaze.com/cloud-storage/pricing)
