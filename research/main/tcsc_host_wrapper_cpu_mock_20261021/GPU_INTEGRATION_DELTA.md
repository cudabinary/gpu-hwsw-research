# Live integration is not ready for GPU approval

The CPU coordinator, ledger and fail-closed tests are implemented. A live CUDA
backend is deliberately **not implemented**. `backend_for` rejects every name
except cpu-mock before creating an output directory; the default CLI has no
GPU enable option. Do not set inherited historical permit flags or treat this
CPU authorization as live approval.

Before even requesting GPU dispatch, the following limited separate patch
and CPU-only verification would be necessary:

1. Bind a new private live adapter to a separate copy of the preserved guarded
   runner. Preserve its existing preflight, device/PID/engine observations,
   safety thresholds, fresh PID/ACK, independent watchdog, mandatory full arrays,
   cancel checks, release marker and retirement checks. Adapt only the frozen
   three-worker arm layout and four-arm coordinator. No old source is edited.
2. Wire parent markers at their actual Popen/ready/ACK/poll/retirement/validation
   locations and bracket every existing observer call without moving, skipping
   or padding checks. Counts/durations are recorded, not forced equal. Keep
   existing child metrics as raw records; no new event placement or owner binary.
3. Supply real OS accounting for only the coordinator's owned processes through
   their existing handles. Validate coverage and conservative peak aggregation
   with owned non-GPU child fixtures, including missing counter/cleanup cases.
   A mocked number below a cap is not an OS memory guard. Unknown driver memory
   remains unknown. Do not inspect protected or foreign process memory/modules.
4. Bind actual stdout/full-output decoding and independent Python distance
   validation to the backend evidence. Mock booleans cannot replace these checks.
   Verify raw exclusive output paths, failures and stop/no-followup using owned
   non-GPU fixtures. Retain the old strict guard unchanged.
5. Freeze source/configuration/binary/input hashes, confirm the fixed budgets,
   then seek a **new explicit GPU approval**. An execution entry point must be
   separate and require a fresh approved freeze; no simple CPU CLI flag may
   reactivate historical permissions.

Because the original live runner is a monolithic guarded function, connecting
those callbacks requires more than swapping a backend name. No broad guard
refactor was attempted. Stop if safe connection requires a broad rewrite,
foreign/privileged observation, new binary/kernel, installation, relaxed checks
or unaccounted memory. Report the exact boundary before proceeding.

The proposed future boundary pilot remains [7,5,5,7], each target preceded by
the same mandatory micro7 mode7/mode5 workers: at most 12 CUDA workers, 152
full BFS arrays and 8 init-only cancels, serial execution, total wall <=600s,
per arm <=90s, child watchdog 20s, three 60s no-dispatch gaps. Management samples
<=120/arm and 480 overall, raw output <=128 MiB. No new GPU dispatch is made here.

Preserve start free VRAM >=2048 MiB, run free VRAM >=1536 MiB, observed temperature
<78 C, 3000ms telemetry freshness, 2s management timeout, workspace caps and
ISOLATION_UNVERIFIED. Stop on every correctness/CUDA/OOM/watchdog/deadline,
resource/coverage failure, observable foreign research compute, abrupt observed
environment change or unconfirmed owned retirement. No automatic retries,
Nsight, sanitizer, installs, paid resources, OS/security/clock changes or deletion.

That pilot would validate boundaries and compare ready consumers under a common
prepared-state contract. It would **not** validate a strongest cold-service
baseline, concurrent preparation, a GPU builder, S1's physical cause or new HW
need. To claim fair full-service benefit, the absent no-reverse Push path must
first be supplied and verified under a separately approved host-binary scope.
Neither that path nor a final research-direction change is authorized here.
