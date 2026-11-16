# RCC novelty audit

The worktree split focused on modularization, compatibility, and research infrastructure. It preserved the existing direction-optimizing BFS, RIE stopping condition, RCC reachability bounds, and TABLE/LAST caches.

The evidence shows an implementation with exact stopping certificates and some CPU cost reductions. The strongest end-to-end service comparison still needs OLD_P2. A novelty assessment also needs to distinguish RCC from SCC/WCC bounds, reachability indexes, and reuse of earlier traversal results, and compare with strong public implementations across real graphs, cold and warm conditions, and measurement uncertainty.

The scope follows [NOVELTY_SCOPE.md](evidence/previous/NOVELTY_SCOPE.md). The split included no new literature search or comprehensive prior-work audit.

Using reachable sets to narrow the next search remains at DISCOVERY. Establish the applicable conditions, correctness, incremental work avoided, maintenance cost, counterexamples, and performance against a strong baseline before advancing it to VALIDATED or PAPER_CANDIDATE. A paper branch and submission require separate authorization.
