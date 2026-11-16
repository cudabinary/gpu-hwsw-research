# RCC-Scope and DistanceGuard — correctness contract and proofs

## Scope

An immutable directed unweighted multigraph, one source, and an exact distance to every vertex, with `-1` for unreachable. Path counts, all predecessors, weighted edges, visit order, and edge callbacks are outside the contract. The implementation uses one CPU owner.

The graph is held as `shared_ptr<const Graph>`. The reverse index must match the exact graph object. Equal integer versions do not allow cache reuse across distinct graph objects. Output is borrowed until the next request. The benchmark copies the full array for every request to align result lifetime.

## A completed reachable set is closed under outgoing edges

Let `R = Reach(r)` be the exact reachable set from a previously completed BFS. If `u ∈ R` and `(u, v) ∈ E`, then the path from r to u extends to v, so `v ∈ R`. There are no outgoing edges from R to its complement. Incoming edges from outside R may exist.

For a new source `s ∈ R`, `Reach(s) ⊆ R`. This supports three rules.

- Original RCC can stop when the discovered count reaches `|R|`.
- Scope skips Pull destinations outside R.
- Regional RIE can stop when the sum of global indegrees of the still-undiscovered vertices in R reaches zero.

TABLE stores cardinality bounds. Scope retains actual membership and an enumerable vertex list, with a different storage cost.

## Regional RIE uses global indegree

R is outgoing-closed and may have incoming edges from outside. Initializing with the sum of outgoing degrees and subtracting global indegrees can underflow or cause incorrect termination. The implementation starts with the exact sum of global indegrees over R and subtracts the same per-vertex quantity at discovery, keeping the remainder nonnegative.

If the total incoming degree of undiscovered vertices in R is zero, no further undiscovered vertex is reachable from s. This is a sufficient condition.

## Publishing the completed discovery set

The two Direction queues store only the current and next frontier. Scope scans the completed `distance[n]` to construct membership, a vertex list, and the incoming-degree sum. Preparation and the temporary old-plus-new payload are accounted for.

If the source is in the old region and the new reachable count equals its size, containment implies the sets are equal. The old certificate can be retained. A smaller completed set replaces it. If reachability spans the whole graph, Scope skips allocating an explicit list for that whole range.

## DistanceGuard

Retain the previous completed distances `d_r`. The new source s must be reachable from r. At current level l, any vertex v discovered in the next level must satisfy

```text
d_r(v) <= d_r(s) + l + 1
```

A shortest path from r to s followed by a path of length l+1 from s to v gives the bound. A violating candidate is deferred for this level. A later level may discover it.

The current frontier `F_l` gives a tighter bound.

```text
d_r(v) <= 1 + max(d_r(u) for u in F_l)
```

For each actual edge (u, v), `d_r(v) <= d_r(u) + 1`. Also, `max(d_r(u)) <= d_r(s) + l`, so the frontier bound is at least as tight as the source-radius bound.

A vertex without a finite old distance remains outside scope as long as s is in R. A temporary distance horizon expands across levels. Its vertex count cannot serve as a bound on total reachability.

## Preservation of exact output

At each level, the traversal discovers unseen vertices adjacent to the current frontier at distance l+1. Scope and DistanceGuard exclude only destinations proven ineligible at that level. The discovered vertices and frontier match Direction+RIE with the same cardinality bound. The guard with unchanged alpha=15 and beta=24 also matches the number of levels and direction choices. `SCOPE_LOCAL` changes policy inputs and can choose a different direction.

## Failure behavior

Incomplete, failed, and interrupted traversals retain the previous valid certificate and publish no new one. Invalid sources and graph identities are rejected. If certificate payload exceeds the budget or an injected publication allocation fails, the executor returns the completed exact result and skips certificate preparation. Readers can keep ownership of an earlier immutable snapshot.

The budget covers CPU array payload. Allocator headers, RSS, CUDA memory, and indefinite retention of earlier snapshots are outside that boundary. The compact pending list is workspace and can throw a C++ allocation error. `Domain` and `direction()` are internal helpers for trusted certificate or WCC inputs.

## Counterexamples

[Counterexample records](../results/COUNTEREXAMPLES.json) and [verification](../tools/verify_guards.py) cover four cases.

1. Treating partial prefix {0, 1} of 0→1→2 as closed loses vertex 2.
2. For R={1, 2} on 0→1→2, outgoing mass in R is 1 and incoming mass is 2.
3. Frontier MIN can wrongly exclude a true next-level vertex. The proof requires MAX.
4. Marking a temporarily excluded vertex permanently unreachable can corrupt a later result.

These proofs establish sufficient conditions. Academic priority is outside their scope.
