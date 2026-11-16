# Independent novelty audit of RCC-Scope and DistanceGuard — 2026-10-21

**NOVELTY_NOT_ESTABLISHED.** The review verified implementations, exact additional probe savings, and a limited synthetic case. Academic priority, a standalone paper contribution, general end-to-end gains, and a GPU or hardware case remain open. Both extensions stayed outside default RCC.

## Conditions and proof scope

RCC-Scope uses the outgoing closure of `R = Reach(r)` from a completed exact BFS. If `s ∈ R`, then `Reach(s) ⊆ R`, so Pull can restrict destination candidates to R. Regional RIE initializes from the **sum of global indegrees of vertices in R**. The implementation and its counterexample verify that outgoing-edge mass is insufficient. COUNT_ONLY and SCOPE_GLOBAL maintain the same certificate and isolate spatial candidate pruning. LOCAL also changes the direction policy and regional stopping condition.

DistanceGuard uses `d_old(v) <= d_old(s) + level + 1` for the radius bound and `d_old(v) <= 1 + max(d_old(u), u in current_frontier)` for the frontier bound. Every actual edge satisfies `d_old(v) <= d_old(u) + 1`, so a violating destination cannot be reached in the current Pull step. Its eligibility can change at later levels. Frontier MIN and the size of a temporary radius are invalid bounds for frontier eligibility and total reachability, respectively. The audit compared the direct proof with the implementation and finite exhaustive checks.

On the matched Google and LiveJournal cases, FRONTIER reduced reverse-edge probes relative to DIST_COUNT with the same number of levels and vertex checks. This isolates actual candidate exclusion beyond count and RIE stopping in those runs.

## Primary sources reviewed

| Prior work | Mechanism examined | Relevance to this implementation |
|---|---|---|
| [Goldberg and Harrelson, ALT, SODA 2005, §4](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/01/soda05.pdf) | Landmark distances and triangle inequalities give exact lower bounds. | The radius applies an existing distance inequality at a BFS level. Frontier MAX follows from the edge-distance inequality. ALT uses point-to-point A* and the prototype uses an online prior result for a full single-source Pull filter. The audit did not identify an identical implementation. |
| [Akiba, Iwata, and Yoshida, PLL, SIGMOD 2013, §4.2 and §6](https://arxiv.org/html/1304.4661v1) | Labels made by earlier BFS runs prune later expansion and edge traversal, including directed graphs. | Reusing earlier BFS information for pruning precedes this work. PLL constructs and queries a two-hop distance index. This prototype temporarily filters destinations with a single previous runtime array. |
| [Beamer et al., Direction-Optimizing BFS, SC 2012](https://people.eecs.berkeley.edu/~krste/papers/beamer-sc2012.pdf) | Top-down and bottom-up switching and early exit from Pull neighbor scans after a parent is found. | Direction switching and probe avoidance are established. The frozen P2 and RIE are internal controls from that family. |
| [GAP author's BFS implementation](https://github.com/sbeamer/gapbs/blob/master/src/bfs.cc) | A parent array, sliding queue, bitmap, and parallel Push/Pull, with defaults alpha=15 and beta=18. | The internal reference uses alpha=15 and beta=24. The audit inspected source. A matched public baseline for complete distances, preparation, and output remains open. [Raw source](https://raw.githubusercontent.com/sbeamer/gapbs/master/src/bfs.cc) |
| [O'Reach, SEA 2021](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2021.13) | Static Boolean reachability indexing, with build, query, and memory comparisons. | RCC-Scope needs comparison with reachability indexing and set reuse. O'Reach Boolean query time was excluded as a denominator for the full owned array. |
| [SlimSell, author version](https://arxiv.org/abs/2010.09913) | BFS representation, vectorization, and work reduction. | The audit verified the supplied reference. It made no claim of algorithm equivalence or direct performance comparison. |

## Standalone contribution

The implementation retains one completed online result in a 4n-byte distance array, computes MAX in the existing frontier bitmap loop, uses exact temporary candidate exclusion, and updates its state without a preprocessing index. These are concrete design properties. Priority over related work remains unestablished.

The study found no stable full-service advantage against strong baselines on real-world-derived inputs. The positive condition used a deliberately designed synthetic graph, localized requests, and a ready reverse index. It failed with cold preparation or distinct sources. Strong public implementations, new real-world workload or graph holdouts, and a validated selection policy with measured cost remain open. The screening rule across 40 conditions and several candidates did not adjust for multiple comparisons.

Keep both extensions as independent experiments, with the counterexamples and mechanism evidence. The current status remains outside default RCC and below the threshold for a standalone paper or hardware contribution.
