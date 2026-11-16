# Novelty and the hardware question

Direction-optimizing BFS, EARLY_N, containment between completed reachable sets, WCC bounds, and result caching apply or combine existing software methods. The exact metadata supports a proof of the RIE stopping condition. Academic priority needs separate review. New hardware, a novel GPU runtime algorithm, and a novel partial index remain unestablished.

An effective reverse-index consumer and inexpensive termination certificates can skip measurable work. Any hardware comparison must account for required output writes of n elements, additional reverse reads and construction, GPU atomics, and host synchronization at level boundaries. The results did not establish a need for a dedicated Shadow Engine.

On the GPU, RIE used already collected statistics to skip the final unnecessary level, and Push+RCC skipped levels using a prior completed result. These observations do not identify the dominant SM, L2, or DRAM constraint or establish that new hardware beats strong software. The decision is CONTINUE_SW. The hardware question remains open.
