# One exact WFA source archive restored; no paper code changed

Operation: `wfa-corrected-source-20261021-one-pack-01`, complete at
2026-10-21 04:24:12.581 UTC. This was a source-recovery operation, not a WFA
experiment or a MAIN direction change.

Protected destination, relative to the MAIN task root:
`RESEARCH_ARCHIVE_FULL_BACKUP_20261021/WFA_CORRECTED_SOURCE_RESTORE_20261021/`.
The paper owner can read `HANDOFF_WFA_SOURCE.md`, `RESTORE_RECEIPT.json`, the
archive and `members/WFA-GPU/` there. Do not restore into an old cleanup path.

* Evidence ID: `WIN_PAPER/rtx4060ti_wfa_mechanism_20261019/source/WFA-GPU_corrected.tar.gz`
* Archive: 1,108,320 bytes; SHA-256
  `6519a817e52d72e74938937b7397ad653b319dde5652843a2c311e9d644e232f`.
* Single downloaded pack: 67,108,864 bytes; SHA-256
  `881c2823242d2d359c3ba83e9f3cc3ebc7336653635fc9e3183d36fee0c797fb`.
* Pack index 329; archive offset 50,705,464, length 1,108,320, file offset 0.
* Remote private object name:
  `research-archive/packs/sha256/88/881c2823242d2d359c3ba83e9f3cc3ebc7336653635fc9e3183d36fee0c797fb.pack`.

Full pack hash, logical archive hash, gzip CRC and eight requested original
member hashes were checked. Corrected `align.cu` and `wfa_cpu.c` match both
preserved reference hashes. No missing function/header was reconstructed,
source executed, native WFA build performed or paper repository modified.

`copyInResults` is actually defined at `lib/sequence_alignment.cu:346` and
declared at `lib/sequence_alignment.cuh:88`. It issues two asynchronous D2H
copies and contains no synchronization. READY therefore still requires stream
completion; no actual ABI sizeof measurement or GPU copy test was performed.
The archive supplies original `wfa_types.h` and `alignment_results.h`.

## Canonical transfer accounting

Historical MAIN cumulative counters and the independent task-2 completed delta
were adopted once using the reconciliation seed; legacy counters were not
rewritten. The OS single-writer lock covered reservation, transfer and verification.
State revision 4 records this operation COMPLETE:

| Counter | Bytes |
|---|---:|
| Upload/storage upper bound | 51,754,334,411 |
| Download reserved, including this actual 64 MiB read | 72,911,875,919 |
| Separate future checkpoint upload hold, unconsumed | 4,194,304 |
| Separate future checkpoint download hold, unconsumed | 4,194,304 |

The restore was not charged against the 4 MiB checkpoint hold. No upload was
made by this operation. Recorded limits remain 60 GB storage/upload, 85 GB
download and USD 5 monthly/initial estimates. Conservative rate arithmetic
remains below those estimates; actual account billing, tax, FX and unrelated
account activity are unverified. This is not an invoice confirmation.

The old Paper Scout raw-restore entry point now queues for the MAIN single
writer before authentication/transfer if canonical state exists. It does not
silently bypass the ledger. No automated raw B2 reads should be presumed to
continue independently. Git-based audit remains available. The local canonical
state path is recorded in the private restore receipt; credentials are omitted.

The raw receipt embeds the original retrieval-plan source status
`PINNED_NOT_DOWNLOADED_OR_RESTORED`; that is copied historical plan metadata.
Its top-level verified completion and member hashes describe this completed restore.
