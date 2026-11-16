# Integrated consumer implementation

The three pinned sources for the graph, reverse builder, and P0/P2 under `frozen/consumer` match the originals. The original `frozen/bridge/stop_bridge.hpp` was also preserved. For Direction traversal, the adapter in `include/adapter.hpp` uses the audited bridge logic for exact remaining indegree, the bitmap, and thresholds alpha=15 and beta=24. Push preserves FIFO order and stops at a safe row boundary once the distinct discovery count reaches n or a valid prior certificate bound.

The 17 comparison modes were OLD_P0, OLD_P2, PUSH_N, DO_N, DO_RIE, PUSH_RCC_LAST, PUSH_RCC_TABLE, DO_RIE_RCC_LAST, DO_RIE_RCC_TABLE, PUSH_TABLE_OFF, DO_RIE_TABLE_OFF, PUSH_LAST_OFF, DO_RIE_LAST_OFF, PUSH_WCC, LAST_RESULT_REUSE, DO_N_RCC_TABLE, and DO_N_TABLE_OFF. OFF modes pay the same TABLE or LAST maintenance cost and disable its stopping condition. WCC applies the supplied union-find method to the same graph, paying for a complete CSR scan and `12n` bytes for parent, size, and bound arrays.

The new contract returns a complete distance array as `shared_ptr<const Output>`. The array remains valid after the next request or executor destruction. LAST retains ownership of the result, and TABLE scans the completed `distance[n]` array. The original bridge's LAST result borrowed a scratch buffer valid until the next call. Only LAST_RESULT_REUSE can return the same immutable result directly for a repeated source. It accounts for memory and aliases separately.

Early termination skips the remaining rows or levels and their checks. Direction still needs the complete reverse index and pays for count, scan, and scatter. Push+RCC requires no reverse index and avoids building and storing it. Savings already supplied by RIE are counted only once.
