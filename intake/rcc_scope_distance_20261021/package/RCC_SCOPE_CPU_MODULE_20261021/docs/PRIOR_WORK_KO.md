# Targeted prior-work check

This round focused on implementation and falsification. The reviewed primary sources establish related mechanisms. A comprehensive novelty audit remains open.

1. Switching between Push and Pull according to frontier size is established. This package compares against the supplied Codex policy with alpha=15 and beta=24. [Beamer, Asanović, and Patterson, Direction-Optimizing Breadth-First Search, SC 2012](https://www.scottbeamer.net/pubs/beamer-sc2012.pdf)
2. GAP provides a public high-performance reference. This study did not download, build, or run it. A direct performance comparison remains open. [GAP BFS implementation](https://github.com/sbeamer/gapbs/blob/master/src/bfs.cc)
3. Landmarks and triangle inequalities for shortest-path lower bounds are established. DISTANCE_RADIUS and FRONTIER_MAX apply related inequalities to a temporary BFS candidate set. The original work targets point-to-point queries. This study targets complete single-source arrays using a previous online result. The different output contract leaves novelty open. [Goldberg and Harrelson, Computing the Shortest Path, SODA 2005](https://www.microsoft.com/en-us/research/publication/computing-the-shortest-path-a-search-meets-graph-theory/)
4. Prior BFS labels can prune later BFS traversals. This prototype retains one previous runtime array. It did not build the PLL labeling and query system or benchmark it directly. [Akiba, Iwata, and Yoshida, Pruned Landmark Labeling, SIGMOD 2013](https://arxiv.org/abs/1304.4661)
5. SlimSell jointly addresses BFS work and layout. It supplies context for the costs of representation and vectorization. [Besta et al., SlimSell, IPDPS 2017](https://arxiv.org/abs/2010.09913)

The concrete experiment asks whether one completed runtime result can justify skipping irregular memory requests at low cost. This package did not establish a CPU time advantage on real-world-derived inputs. General system and hardware novelty remain unestablished.
