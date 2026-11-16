# RCC novelty audit

The latest [paper comparison](research/SCOPE_DISTANCE_NOVELTY_AUDIT.md) and [independent implementation audit](research/SCOPE_DISTANCE_AUDIT_RESULTS.md) reproduced additional exact candidate exclusion and a conditional synthetic result for the supplied RCC-Scope and DistanceGuard package. A strong full-service advantage on real-world-derived inputs, academic priority, and a standalone paper contribution remain unestablished. The review consulted ALT, PLL, direction-optimizing BFS, GAP, O'Reach, and SlimSell. Both extensions stayed outside default RCC.

The worktree split focused on modularization, compatibility, and research infrastructure. It preserved the existing direction-optimizing BFS, RIE stopping condition, RCC reachability bounds, and TABLE/LAST caches.

The evidence shows an implementation with exact stopping certificates and some CPU cost reductions. The October 21 matched service comparison closed the OLD_P2 gap under fixed conditions. RCC did not beat ready OLD_P2 on the original LiveJournal input. A novelty assessment also needs to distinguish RCC from SCC/WCC bounds, reachability indexes, and reuse of earlier traversal results, and compare with strong public implementations across real graphs, cold and warm conditions, and measurement uncertainty.

The scope follows [NOVELTY_SCOPE.md](evidence/previous/NOVELTY_SCOPE.md). The split included no new literature search or comprehensive prior-work audit.

## Initial targeted literature check — 2026-10-21

The OLD_P2 follow-up included a targeted primary-source check.

- Beamer, Asanović, and Patterson use frontier-based top-down and bottom-up switching to reduce BFS work. Frozen P2 is a strong baseline from that family and beat RCC on the original ready input. Its performance is specific to the frozen implementation. [Direction-Optimizing Breadth-First Search, SC 2012](https://people.eecs.berkeley.edu/~krste/papers/beamer-sc2012.pdf)
- Hanauer, Schulz, and Trummer use a linear-size index for many static-graph Boolean s-to-t reachability queries and report build, query, and memory costs. A Boolean answer has a different contract from an owned full distance array. Their query timings were excluded as direct full-BFS denominators. The contract comparison suggested checking O'Reach in later scope-pruning and reachability-certificate audits. [O'Reach, SEA 2021](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2021.13) · [Author implementation](https://github.com/o-reach/O-Reach)
- Akiba, Iwata, and Yoshida prune BFS with previously constructed distance labels, supporting exact shortest-distance queries. At the OLD_P2 checkpoint the DistanceGuard ZIP was still unopened. The planned comparison covered preprocessing, label maintenance, output of all n distances, and correctness conditions. [Pruned Landmark Labeling, SIGMOD 2013](https://arxiv.org/abs/1304.4661)

Path concatenation establishes `s in Reach(r) => Reach(s) subset Reach(r)`. Reaching that set-size bound in a completed exact search gives a valid stopping certificate under the immutable-graph and owned-output contract. That proof, passing tests, and some reductions in CPU time leave academic priority and independent paper contribution open.

The OLD_P2 checkpoint decision was **CONTINUE_SW / NOVELTY_NOT_ESTABLISHED**. It preceded inspection and execution of the two supplied modules. The later review linked above evaluates them against the earlier RCC variants, OLD_P2, and Direction+RIE.

Using reachable sets to narrow the next search remains at DISCOVERY. Establish the applicable conditions, correctness, incremental work avoided, maintenance cost, counterexamples, and performance against a strong baseline before advancing it to VALIDATED or PAPER_CANDIDATE. A paper branch and submission require separate authorization.
