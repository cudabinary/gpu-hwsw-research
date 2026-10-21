# Read-only review of the GPU observability block

Scope: existing source and saved logs plus official documentation. No denied
process query retry, new GPU query/execution, privilege/security change, new
allowlist entry or guard modification. The user cannot unlock the PC now; no
repeat unlock request is made. The old blocked capture remains immutable.

## 1. Why did this preflight require LogonUI modules?

`tools/freeze_gpu_baseline.ps1:14` enumerates every process in the GPU process
table, including graphics entries; it does not first restrict the list to CUDA
compute contexts. Lines22-29 preserve only a previously approved exact DWM
identity exception. Line35 sends the other PIDs to the native process guard.
`tools/process_guard.cpp:11` requests PROCESS_QUERY_INFORMATION|PROCESS_VM_READ,
then line15 enumerates loaded modules. Line18 rejects a CUDA/compute DLL prefix.
Unreadable module inventory is rejected before the baseline can be frozen.

Thus LogonUI reached a generic conservative inventory rule. This is a local
safety policy, not a documented CUDA requirement to inspect LogonUI memory.
Even a loaded compute DLL indicates capability, not necessarily an executing
kernel. The raw failed attempt did not persist LogonUI's GPU process type, so
its actual compute/graphics classification cannot be recovered from these logs.

## 2. What does the failure establish?

The frozen guard returned its module-access-unavailable path. The later saved
CIM record reported name LogonUI.exe and a null executable path. The native
guard did not emit its exact Win32 last-error value. It did not establish the
image's protection classification, current lock state, concurrent CUDA activity
or why the requested rights were unavailable. Those remain UNKNOWN.

Windows checks requested process rights against access control, and protected
process rules restrict query/VM-read rights. These explain why a legitimate
process can be unreadable; they do not prove this PID's exact protection mode.
See [Microsoft process rights](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights).
Unlocking might change process presence, but no before/after experiment exists.
The denial is not a CUDA error, BFS correctness failure or proof of interference.

## 3. Official observations that do not read protected process memory

| Candidate | Documented information | What remains unproved here |
|---|---|---|
| Native NVML compute-context enumeration | A compute-context PID list distinct from graphics contexts | Support/permissions/completeness on this driver and RTX4060Ti; no API call was attempted |
| Native nvidia-smi process type | Compute, graphics and mixed context classification | This capture omitted the failing PID's type; missing data cannot be treated as an empty compute list |
| Windows VidSch/VidMm engine telemetry | Scheduler/memory-manager activity across APIs | Engine labels do not isolate CUDA work or guarantee no shared-core interference |
| WSL NVML | Platform-dependent management information | WSL's documented query limitations prevent assuming an empty list proves no workload |

The [NVML API](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html)
documents nvmlDeviceGetComputeRunningProcesses_v3 as compute-context information,
without listing graphics applications. This is different information from a
denied module list, not a method to obtain that denied list. Unsupported or
permission-denied results must remain UNKNOWN, not zero processes. A context
list is a point-in-time observation and does not reserve future GPU access.

[nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
distinguishes compute/graphics process types and notes that WDDM per-process GPU
memory reporting is unavailable. It describes exclusive compute modes, but mode
changes require privilege and are outside this request. No device capability
probe or configuration change was performed.

[Microsoft's GPU telemetry explanation](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/)
attributes the data to Windows scheduling/memory management and explains that
3D and compute engines can share cores. Accordingly, a 3D label does not prove
the shader/memory resources are uninvolved in the measurement.

The [WSL guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) still lists
management-query limitations. These are WSL-specific and must not be silently
transferred to the native Windows path; native support remains separately
unverified. The [Windows CUDA guide](https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html)
excludes ordinary GeForce GPUs from TCC support. No driver-mode change is proposed.

## Decision

Official observation interfaces exist, but an adequate nonprivileged isolation
proof for this exact environment has not been demonstrated. A future protocol
could distinguish observed quiescence from enforced exclusivity, explicitly
validate native capability/return-code semantics and retain uncertainty about
unsampled activity and graphics contention. That is a design-review candidate,
not an approved replacement guard. The current module/identity/VRAM/temperature/
watchdog criteria remain unchanged and the GPU run remains blocked.

The existing module scan itself cannot enforce future exclusivity: it observes
a snapshot and has no authority to prevent a later context or DLL load. Do not
claim it gives a stronger guarantee than its sampling actually supports.

New GPU BFS and performance remain zero/UNKNOWN. No performance or hardware
claim changes. Continue only permitted CPU source/contract reasoning until an
authorized and validated measurement precondition exists. The user being away
is an operational fact, not a reason to request wider rights or bypass security.
