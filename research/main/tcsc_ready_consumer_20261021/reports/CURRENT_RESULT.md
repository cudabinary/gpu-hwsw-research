# Result: blocked before CUDA worker creation

The fresh baseline attempt stopped after 9.563 seconds. The native module
inventory could not open GPU-listed PID 29476. A subsequent CPU-only CIM lookup
identified `LogonUI.exe`, creation time 2026-10-21T12:09:10.081794+09:00, with no
readable executable path. This is an OS logon/lock UI process name, not evidence
that a competing CUDA workload was executing. The exact Win32 last-error code
was not emitted by the frozen guard; do not invent one.

The PowerShell baseline command ran and failed. This was not an automatic tool
approval rejection. No exception/allowlist was added, no process was terminated,
no permissions changed and no CUDA worker was created. The finite dispatcher
was never entered. New GPU BFS=0, GPU cancellation tests=0, GPU builder=0,
Nsight=0. All new GPU timings and ready-consumer utility are UNKNOWN.

The host implementation is concrete: fixed q32, six predeclared consumer modes,
owned full-array return, post-batch raw array capture, exact reference checking,
work reconstruction, fixed input/order/thresholds, fresh-identity handshake,
continuous Windows+WSL guards and independent PID/creation-time watchdog.
The CUDA kernel source/cubin remains unchanged. The CPU replay passed 402 full
arrays and four negative argument cases. These are CPU results, not GPU PASS.
The independent watchdog passed disposable normal-exit and deadline tests.

The first shell compiler invocation could not find cuda.h. A CPU-only include
probe then succeeded, and structured argv compilation succeeded with the
existing compiler and header. No installation or header change was made by
this round. The first invocation's precise failure cause remains unconfirmed.
The final native binary is pinned separately from historical pilot binaries.
The cubin was copied unchanged from MAIN's existing static build. Its hash is
7cea25e119f9e1abbc583cb423db03db5d84f67c1b0dc02cc7170d3ef6b12836,
not the historical pilot's ef333a... hash. The source is unchanged but runtime
validation of this particular static binary remains unperformed. The planned
functional gate would have tested it before accepting any performance data.

The final host includes a new frontier-outgoing-zero stop guard. Its safety
follows from the exact frontier degree sum and was CPU tested. Its actual GPU
execution in this owner has not been tested. Previous Direction/RIE GPU pilot
correctness does not validate this new host or common RCC API GPU compatibility.

The q32 protocol remains a fixed-batch amortization experiment. It contains no
request arrival trace. There is no basis to estimate online request/change rates,
new Plan-A interference, joint preparation completion or HW resource contention.
No old 18.92% slowdown or CPU timing was substituted for these missing values.
