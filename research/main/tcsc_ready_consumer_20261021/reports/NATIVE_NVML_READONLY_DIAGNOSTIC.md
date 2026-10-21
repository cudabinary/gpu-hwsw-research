# Native Windows NVML observation: usable response, isolation unproved

## Scope and actual result

After the WFA one-pack restore, the separately authorized diagnostic ran once
from 2026-10-21 04:28:45.905 to 04:28:46.142 UTC. It used installed native
Windows NVML/nvidia-smi only. No CUDA execution API, kernel, warmup, profiler,
process-memory/module query, denied-process query retry, guard change,
installation or privilege/security change was performed. No benchmark resumed.

| Observation | Actual return | Meaning supported by this observation |
|---|---|---|
| NVML initialization, driver/version, device handle/name | Success (0) | The public read-only library path responded |
| Driver / NVML / device / driver model | 610.88 / 13.610.88 / RTX 4060 Ti / WDDM | Native Windows observation, not a WSL test |
| `nvmlDeviceGetComputeRunningProcesses_v3(device, &count, NULL)`, initial count 0 | 7, `Insufficient Size`, reported count 32 | Documented count-query path responded; this is not an empty list or a buffer-allocation failure in our code |
| `nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv` | exit 0; 32 rows | Names were returned for 30 rows; two were `[Insufficient Permissions]`; every memory value was `[N/A]` |
| `nvidia-smi --query-gpu=name,driver_version,driver_model.current --format=csv` | exit 0, WDDM | Per-process memory cannot be assumed available |
| NVML shutdown | Success (0) | Normal library shutdown only |

Raw stdout/stderr, command timestamps and hashes are in
`audit/native_nvml_readonly_20261021/RESULT.json` and its six log files.
The count probe deliberately requested no record array: no uninstalled header
or guessed `nvmlProcessInfo_t` ABI was used. The separate CLI supplies the saved
PID/name snapshot. These are sequential observations, not an atomic joint view.

The returned names include ShellHost, Explorer, browser/UI applications and two
unreadable names. Those names do not establish that the processes are graphics
only, nor that they execute CUDA kernels. The CLI query did not include process
type. A nonzero reported count cannot be relabelled as zero competing compute
contexts. The raw probe label `COMPUTE_CONTEXTS_REPORTED` describes the API's
reported count, not 32 independently verified CUDA workloads.

## Documentation and limits

The [NVML reference](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html)
defines this API as compute-context enumeration and permits the NULL-array count
call. Return 7 requests a larger array; unsupported, no-permission and other
errors must remain distinct from a successful empty observation. This test
establishes a response from this entry point, not complete coverage or accurate
CUDA-versus-graphics attribution in this environment. No controlled known-CUDA
positive/negative coverage experiment was performed.

The [nvidia-smi reference](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
documents WDDM's missing per-process GPU-memory information. `[N/A]` is not zero.
A missing name does not make the PID harmless. A context can exist without an
executing kernel; a point-in-time list cannot prevent later GPU work. Graphics
activity can still compete for shared resources. WSL support and visibility
were not probed and cannot be inferred from native Windows success.

The original LogonUI inventory failure remains an observability gap. Its exact
Win32 error, protection mode, lock-to-denial causality and concurrent CUDA state
were not established. This diagnostic did not retrieve its denied module data.
No new protected-process investigation or unlock request is needed for this report.

## Proposed measurement contract -- review only

This is not a replacement guard implementation or permission to dispatch.

1. Keep resource and failure limits: fresh telemetry, start free VRAM >=2048 MiB,
   run free >=1536 MiB, temperature <78 C, child watchdog 20 s, request workspace
   <=32 MiB, no retry, finite pinned workers, exact correctness gate and verified
   worker/context teardown. Unavailable safety telemetry stops the run.
2. Distinguish four claims: API availability, observable context coverage,
   sampled quiescence and enforced exclusivity. A successful count call proves
   only the first here. Neither the original module scan nor this alternative
   enforces exclusive future GPU access.
3. Before changing preflight, resolve the reported nonzero context population
   and the two unreadable identities through an agreed, supported observation
   contract. Do not add UI exceptions based only on names or silently discard
   nonzero entries. Any unavailable or ambiguous coverage remains UNKNOWN and
   cannot satisfy an absence-of-other-compute requirement.
4. A future coverage check must specify native Windows versus WSL and what
   known workload it can detect. Such a check would itself need separate
   coordination before any CUDA execution; none was run now.
5. If an observable-isolation protocol is later accepted, describe its sampling
   interval and blind spots, retain graphics activity/telemetry and paired run
   order, and invalidate affected performance blocks on observed contention.
   Repeated 0% utilization or empty lists are not proof of exclusivity.
6. Do not alter protected-process permissions, driver/compute modes, terminate
   UI/research processes, disable guards or automatically resume this dispatcher.

Decision: **current alternative has not demonstrated the same isolation
objective. GPU benchmarking remains on hold pending coordination.** New GPU BFS,
cancellation checks and GPU builder tests remain zero. Ready-consumer utility,
new Plan-A interference and hardware residuals remain UNKNOWN.
