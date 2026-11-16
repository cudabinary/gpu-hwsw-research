# Next steps for MAIN

The research goal is GPU architecture and hardware–software co-design at the level of ISCA, MICRO, HPCA, or ASPLOS. BFS, TCSC, and RCC form the first case study.

1. Select a validated software consumer through the shared API. Resolve the missing OLD_P2 service baseline in the RCC track. Review RCC changes before integrating them.
2. Implement and validate the shared CUDA API backend. The historical native owner ran a correctness pilot. CUDA module substitution through the shared API remains open.
3. Define a separate GPU measurement plan. After establishing a strong software baseline, distinguish instruction and atomic costs, SM residency, L2 and DRAM traffic, and launch and synchronization overhead. Establish causes and the need for hardware with measurements.
4. Distinguish the knowledge, control, and timing gaps. The immutable CSR exists before A. A row-completion interface can delay access to information already present in that CSR.
5. Once measurements establish a structural bottleneck, test whether it generalizes to other GPU workloads. Account for data movement, finite bandwidth, and required output writes.

The worktree split ended before any new algorithm or GPU performance experiment.
