# Archive-first evidence access after authorized local cleanup

This additive availability ledger updates local path presence for archived file
versions. It does not change the immutable archive checkpoint or scientific
claims. Join `location_id` AND `sha256` to the parent evidence index.

`LOCAL_REMOVED_REMOTE_ARCHIVE_RETAINED` means the exact archived version was
rehashed immediately before local removal and its path was absent at the final
audit. Access it through the pinned private B2 recovery checkpoint. GitHub stores
the index, not every raw experiment payload. Permission to read GitHub does not
grant B2 access. Never treat unread payloads as scientifically verified evidence.

`LOCAL_CHANGED_RETAINED_ARCHIVED_VERSION_OLDER` means a newer local version was
kept; it is not silently covered by the older archive. Other KEEP/SKIP states are
recorded separately. New/unmanifested files were not targeted. The supplemental
live Scout state remains protected; this ledger covers the frozen source manifest.

MAIN/RCC active worktrees, application runtime, backup control and credentials
were retained. Historical directories can remain empty or contain excluded Git,
environment or newer files. No recursive directory removal was performed.

Paper Scout now uses exact GitHub commits/blobs plus bounded authenticated B2
reads into a new audit materialization directory. A real archived report readback
was SHA-256 verified. The existing hourly schedule and scientific judgments were
preserved. Research source files and RCC history were not changed by this task.

The user explicitly requested cleanup without another independent-device copy.
Private B2 is therefore the sole verified off-PC copy for many retired payloads.
The prior independent restore used a fresh isolated process/output on the same
PC, not another physical computer. Full content verification was performed;
the full logical directory tree was not physically re-created in its entirety.

To recover: read the parent ROOT_RECOVERY_LOCATOR.json and RESTORE.md; use the
authenticated byte restorer in a new empty destination, select Evidence ID/root,
and verify the returned hashes. Keep native POSIX naming and the SQLite snapshot
application map where needed. Do not overwrite active originals. Current finite
transfer/key expiry limits still apply; a complete future restore may need fresh
transfer approval and a newly scoped key. Never put keys in Git or chat.
