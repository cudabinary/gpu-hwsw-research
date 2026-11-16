# Missing strongest baseline for the full service

Original P2 was the strongest non-RCC resident consumer on LiveJournal. The initial service gate omitted it. Push+RCC_TABLE beat PUSH_N and measured sequential DO_RIE. Whether it beats original P2 under the same cold or ready owned-output service contract remained open at this checkpoint.

The three original CPU workers had finished and no additional workers were run. P2 service times were never reconstructed from existing components. The historical Consumer-first P2 result had a different source and contract and was excluded as a direct denominator.

The minimum follow-up uses the existing data structures and thresholds.

- Keep the LJ4096 original input and order. Use relabeling to test order sensitivity.
- Include frozen P2 deferred and ready paths, PUSH_N, and Push+RCC_TABLE.
- Use q8 and q32, complete owned output, the frozen builder, and a fixed A.
- Preregister three processes, seven rounds, and counterbalanced run order. Keep the original paths and seeds fixed after inspecting results.
- The missing comparison is a CPU service experiment.

This document records the proposed follow-up at the original checkpoint. The earlier CPU run reached its allotted measurement budget.
