# Reproduce the bounded attribution accounting

Read ATTRIBUTION_VERDICT.md first. This is logical work accounting, not a GPU
measurement, CPU timing benchmark or rerun of the previous correctness suite.
No executable, kernel, builder or original input was changed by this task.

Inputs are the existing pinned owner/kernel/builder source and the two fixture
files. ACCOUNTING_SCOPE.json records their SHA-256 values. The source-ordered
incoming lists match the frozen CPU builder's scatter order; no GPU row-order
change is assumed. Frontier partitions are computed once for each of the fixed
64 graph/source combinations. The six policy paths are then accounted from
those partitions. They are not six independent correctness implementations.

In a new isolated copy containing the same src/include/fixtures/config trees
and these two analysis scripts, with no prior output at the analysis path:

```text
python tools/account_consumer_attribution.py
python tools/account_static_bound.py
```

The scripts refuse existing output directories. Preserve previous results;
choose another isolated copy for reproduction rather than deleting originals.
Do not invoke run_gpu_round.py or run_one_session.py to reproduce this audit.
No driver, management query, compiler, profiler or existing owner is invoked.

Files:

* query_work.csv: 384 policy/query accounting rows for existing modes.
* level_work.csv: logical operations at each processed level.
* prefix_work.csv: sums at q1/q2/q8/q32, not request arrival experiments.
* contrasts.csv: signed differences for predeclared existing mode pairs.
* static_bound/: algebraic identity and projected Push controls derived from
  saved accounting. These controls are not implemented in the GPU owner.
* SOURCE_CODE_MAP.json: exact matching source lines used by the verdict.
* MINIMUM_CONTRAST_PROPOSAL.json: fixed review proposal; dispatch remains false.
* SHA256SUMS: analysis inputs/scripts/output identities relative to the round.

"Atomic", "copy" and "kernel" counts are calls implied by valid code paths,
not measurements of issued instructions, DRAM traffic or elapsed GPU time.
Kernel scheduling can reorder frontier entries; these counts depend only on
fixed frontier membership and incoming-list order. No GPU trajectory check was
possible, so the future functional gate remains necessary. Existing safeguards
and the immutable GPU pre-registration file remain unchanged.
