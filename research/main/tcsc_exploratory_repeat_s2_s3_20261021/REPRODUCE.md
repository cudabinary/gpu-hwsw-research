# Reproduction and provenance

## Safe offline verification

Use Python 3 with only its standard library, from this extracted directory:

```text
python tools/reproduce_analysis.py
```

This reads the bundled S1/S2/S3 receipts and successful CSV tables, recomputes
all q-prefix paired ratios and new-run counts, verifies output-array SHA-256,
and checks execution pins. It does not query a GPU, launch CUDA, compile,
change files, or require the old sibling project. The bundled original
`tools/analyze_campaign.py` is the exact postprocessing source used here;
it expects the original sibling project and refuses an existing output folder.
Use the standalone reader above to verify an extracted delivery instead.

`SHA256SUMS` covers package files, excluding itself and local-only delivery
metadata. The ZIP verification receipt outside the archive records CRC,
member-hash and whole-archive SHA-256 validation. Git contains a path-redacted
text derivative. `PUBLICATION_MAP.json` records raw and published hashes;
those sanitized JSON bytes must not be confused with original execution bytes.
Raw XML, binary arrays, executable and cubin are in the private delivery ZIP.

## Historical execution (do not rerun without a new authorization)

The following command was executed once in the original Windows round folder:

```text
python tools/run_campaign.py --exploratory-isolation-unverified
```

The coordinator uses exclusive result folders and refuses an existing campaign;
it ran exactly S2 and S3 with a combined 600-second wall deadline. Each session
had six CUDA workers, 134 BFS arrays and two initialization-only cancellations.
The source/input/binary pins are in `config/PLAN.json`; its SHA-256 is
`cbb1459e2540e0ed8598bc681647a93e27d8c4003a9d15c98167e859944d12a4`.
The installed driver reported 610.88. No new C++/CUDA build was performed.
`audit/RUNNER_SCOPE_DIFF.patch` preserves orchestration differences from S1.

S2: smoke modes 5/7 on sources 0/1/4, then timing modes [5,7]/[7,5].
S3: smoke modes 7/5, then timing modes [7,5]/[5,7]. Timing sources were 17*i,
i=0..31, on the unchanged 4096-vertex, 48292-edge LiveJournal derivative.
q1/q2/q8/q32 are nested request prefixes of each fixed batch, not independent
online arrivals. No warmups or automatic retries were used.

The 20-second owned-worker watchdog, VRAM thresholds (2048 MiB before,
1536 MiB during), observed temperature <78 C, 32 MiB request workspace,
telemetry freshness and observable-foreign-compute stops stayed enabled.
No foreign process module/memory or protected-process queries occurred.
Isolation remained unverified throughout; no low-utilization or empty-list
observation is claimed to prove exclusive GPU use.

## Analysis provenance and boundaries

One CPU-only postprocessing attempt wrote a partial CSV and stopped because
smoke and timing dictionaries had different field sets. No CUDA run failed or
was repeated. The field was normalized, and a new `analysis_complete` directory
received the successful offline result. The partial files and explanatory
`audit/OFFLINE_ANALYSIS_FORMAT_NOTE.txt` are retained.

The original C++/CUDA code remains byte-identical to host_controls_v1. The
mode7 lean static-bound Push avoids dynamic policy statistics. Mode5 Direction
has its original dynamic statistics, bitmap and transition costs. They are
practical comparison paths, not instruction-matched variants. The earlier
mode8 control remains in S1, but this approval did not rerun it. No public
state-of-the-art GPU BFS implementation was added or defeated by this result.

CPU graph loading, reverse building, reference generation and native setup/H2D
are outside ready-resident prefix timing and separately recorded. The native
setup timer includes context/ACK/allocation, so it is not a pure transfer timer.
Initialization, level control/synchronization, safety checks, complete output
copy and owned-output publication are inside the request boundary. Stream
event intervals may include host gaps and are not kernel busy time. Worker
wall windows include host work. Work counts reconstructed by the host are not
DRAM/L2 traffic measurements. No GPU builder or D0-D3 experiment was run.

The approval and source preservation references in the plan record historical
provenance, not a reusable future execution permission. Changing result paths
or deleting a lock to rerun would require a separately reviewed plan.
