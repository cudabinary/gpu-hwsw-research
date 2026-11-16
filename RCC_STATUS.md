# RCC status at the worktree split

**Continue independent software validation.** The work has yet to qualify as a paper candidate.

- **Functionality.** The CPU baseline, RCC TABLE, and RCC LAST implement API 1.0.0 and can be swapped in the same MAIN binary. [COMPATIBILITY.json](results/COMPATIBILITY.json) records this checkpoint's results. Earlier results are reported separately because their experiment counts have different scopes.
- **Performance.** On LiveJournal at q32, Push+RCC took about 20% less time than Push+EARLY_N. The strongest overall service path remains unknown because the original OLD_P2 full-service comparison was missing. RCC skipped zero additional work after Direction+RIE. Performance with the shared adapter's diagnostic counters and additional copies remains unmeasured.
- **GPU.** The historical pilot's 36 BFS runs and 12 cancellation checks were verified from its records. The CUDA backend and actual module substitution through the shared API remain incomplete.
- **Next steps.** Compare full service costs with OLD_P2 under a common contract, check effectiveness across graphs and request patterns, and assess against strong public baselines and prior work. Publication readiness and the need for hardware remain open.
- **Dependencies and open items.** The preserved builder, Direction traversal, and bridge depend on g++ and Python, with CUDA 13.3 tools for static builds. Open items include the P2 baseline gap, adapter overhead, the CUDA API backend, dataset coverage, and novelty.
