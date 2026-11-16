# Evidence coverage

The survey covered 16 existing research roots. It excluded the operating system, designated caches, dependency environments, and credentials. The private B2 restore manifest retains the exclusion list, empty directories, and symbolic-link metadata. Restoration avoids blindly following links or pointing them to absolute paths on the original computer.

The validation downloaded all remote data, checked physical object hashes, and reconstructed the original file hashes. A separate Python process restored representative files into a new empty directory without reading the original research paths. See `restore_validation` in the JSON for counts. Validation on a second physical machine and materializing the full logical dataset on disk remain outstanding.

The six SQLite databases have derived snapshots created through online backup in read-only mode (`mode=ro`) and checked with `integrity_check`. The separately copied raw database, WAL, and SHM files have no combined consistency guarantee. Point-in-time consistency across databases remains unverified.

PAPER_SCOUT's `state.json` changed during the first survey. A supplemental version was captured after two matching full reads and validation of the JSON syntax. The running process continued. The initial pending status remains in the historical record, and the final checkpoint links the supplemental location.

Hash verification establishes that CSVs and logs were preserved. Performance claims still depend on the experiment's evidence and scope. Retain the distinctions among CPU measurements, actual GPU runs, synthetic models, static compilation, and plans that were never run. Claims without underlying CSVs or logs still lack that evidence. The earlier evidence index and claim links are preserved in B2.
