# Notes for a later integration review

The independent track supplies two candidate mechanisms and their counterexamples. Evaluate them selectively after the earlier Direction+RIE service integration. The handoff scope excludes a new builder, event queue, or GPU run.

1. `ClosureScope` uses membership of a completed Reach(r) to reduce Pull destination candidates. RCC_TABLE's count alone cannot reconstruct that list. The candidate uses the prebuilt reverse arrays and original alpha and beta policy.
2. `DistanceGuard::FRONTIER_MAX` retains one previous completed distance array (4n bytes) and skips the incoming list of any destination with old distance above the current frontier's old-distance maximum plus one. A buffer swap retains the previous result. A returned copy, retained memory, and output lifetime still have costs.
3. DistanceGuard saved extra probes after RIE even on LiveJournal, where the reachable region is almost the entire graph. Additional label lookups made CPU time worse. Leave it disabled by default.
4. The number of vertices in a temporary radius is unsafe as a termination bound. Exact count, RIE, and completed closure cardinality supply the stopping certificates.
5. A 4-byte label lookup might replace a long incoming scan for an impossible high-degree destination. This remains a hypothesis for GPU performance. Record avoided probes, extra label reads, and checking cost at each level.
6. The mechanism overlaps landmark methods, triangle inequalities, and pruning. Academic priority requires further evidence.
7. Compare on the same backend with existing and newly fixed source orders, sources outside the prior set, repeated-source reuse, graph identity checks, cancellation before completion, and complete distance output.
8. The executor currently has one CPU owner. GPU implementation would add frontier-max reduction, prior and current array lifetime handling, publication, memory, and reduction synchronization costs. The need for hardware remains open.

Preserve ongoing work and its original records. Enable a candidate only where the matched controls show enough benefit.
