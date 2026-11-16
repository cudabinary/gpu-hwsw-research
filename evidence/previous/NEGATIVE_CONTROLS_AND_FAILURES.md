# Negative results, failures, and limitations

The raw records retain timing outliers and losses. The resident consumer and service each have 21 pairs. Statistical significance, noninferiority, and 1% interference were outside this evidence. The new source order was fixed before seeing results. The original and holdout orders were already known. The service ran only the predefined original schedule, leaving generality across other full-service schedules unknown.

The combined path was dropped where RCC avoided zero additional checks after RIE on LiveJournal and its relabeling. Large RCC gains on disconnected synthetic SCCs are specific to those inputs. WCC can supply the same size bound in some synthetic cases. The controls expose the costs of WCC preprocessing and TABLE initialization and updates, as well as simple repeated-source reuse via LAST_RESULT_REUSE. DO_RIE_RCC passed no fixture's full predefined service gate.

CPU and CUDA builds and correctness runs succeeded. The CPU compiler emitted one line-layout warning involving two independent `if` statements. The measured source and executable stayed fixed after measurement. The CPU suite and GPU pilot passed. Sanitizers were outside this checkpoint.

The following issues occurred before the GPU pilot.

- The first GPU engine counter sample returned an error. Execution paused before any CUDA launch.
- An additional sandbox diagnostic could not access the counter object. A separate native diagnostic confirmed 806 NVIDIA samples with status 0. The original error's root cause remained undetermined, and the failing sample was discarded.
- Windows PowerShell 5 policy prevented file-based execution. The run used the existing PowerShell 7 installation with the system policy intact.
- PID 1944 was a protected DWM process, so native modules could not be inspected. The monitor used its previously approved exact PID, name, and creation identity.
- The copied monitor lost fractional seconds when reparsing PowerShell 7 JSON `DateTime` objects. Comparing those objects directly in UTC corrected the issue. The matching tolerance and the VRAM, temperature, and watchdog limits stayed fixed.

There was one actual kernel pilot campaign. Normal GUI contexts were monitored using exact PID, creation time, modules, and GPU engine. Protected OS contexts were monitored using pinned CIM identity and engine activity. GUI shader activity could still occur, so the measured environment differs from a dedicated headless system.
