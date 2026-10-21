# CPU-only reproduction

Python 3 standard library only. No installs, compilations, GPU/device query or
child process is needed. Do not execute any old GPU harness.

Run the small contract suite into a new directory:

```text
python tests/run_mock_tests.py --output results/REPRO_NEW
```

Run one nominal synthetic campaign into another new directory:

```text
python src/host_wrapper.py --cpu-mock --output results/MOCK_EXAMPLE_NEW
```

The CLI's default route without --cpu-mock rejects GPU dispatch. All output
directories and result records are exclusive: an existing path is refused;
do not delete/replace old results to rerun. Failed or completed Campaign objects
cannot restart. Raw ledgers, offending observations, previous successful worker
responses and STOP records remain after failure; stop-record headroom is reserved.
Disk/OS failure that prevents writing cannot guarantee a persisted receipt, but
does not permit another dispatch. The live OS behavior is not validated here.

The first suite has 23 passing cases in `results/CPU_MOCK_TESTS`. Code review
added BaseException/KeyboardInterrupt cleanup handling and an interrupt case;
the final 24 passing cases are in `results/CPU_MOCK_TESTS_V2`. Do not count these
as 47 independent safety checks or actual GPU/CPU BFS executions. Real OS memory
APIs, independent watchdog processes, actual cancellation/preemption, driver/PID
coverage and raw GPU distance validation are outside this mock's coverage.

Every receipt/ledger is labeled CPU_MOCK or SYNTHETIC. Virtual gaps do not sleep.
No synthetic timestamp or memory report is a measured performance/peak value.
The plan contains frozen historical binary/input references for future binding,
not a live authorization. The supplied source preservation hashes only certify
that the inspected original owner/cubin/executable/runner bytes did not change.

`SHA256SUMS` and the delivery ZIP receipt cover this implementation, reports,
configuration and raw mock results. Private Git contains a sanitized text
checkpoint; Library delivery is not a B2 backup/restore certification.
