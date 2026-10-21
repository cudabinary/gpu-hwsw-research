# Latest update: read-only diagnosis complete, no GPU measurement resumed

GPU measurement remains on hold: CUDA workers=0, new GPU BFS=0, timing UNKNOWN.
CPU replay passed 402 full arrays and four negative argument tests. CPU results
do not establish GPU correctness for this new host or static cubin.

The previous module guard failure is an observability gap, not proof of another
CUDA job or of a lock-to-denial cause. No repeated unlock request, denied module
query retry, permission change or guard relaxation was made.

After separate read-only authorization, installed native Windows NVML and
nvidia-smi responded. NVML's NULL-array count call returned Insufficient Size
(7), count 32. CLI returned 32 entries, two unreadable names, all memory N/A on
WDDM. Neither complete CUDA attribution nor measurement isolation is proved.
Read reports/NATIVE_NVML_READONLY_DIAGNOSTIC.md for evidence, official sources
and the proposed measurement contract. This proposal does not authorize dispatch.

One separately requested WFA source archive was restored from one 64 MiB pack
to a protected new folder, verified, and recorded under the MAIN single-writer
ledger. Read reports/WFA_MINIMAL_RESTORE_HANDOFF.md. No paper repo was changed.

Earlier reports, raw failed captures and the original ZIP/Library version are
preserved. reports/OBSERVABILITY_REVIEW.md is the earlier source/document-only
review, before the separately authorized native management observation.
