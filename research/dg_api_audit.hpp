#pragma once
#include "rcc/v1.hpp"
namespace dg_audit {
// Optional experiment-only telemetry. This is not an addition to API v1.
struct Phases {
 bool enabled=false,exact_edge_counter=true;
 double prepare_graph_ns=0,prepare_reverse_ns=0,prepare_workspace_ns=0;
 double allocation_ns=0,algorithm_ns=0,copy_ns=0,maintenance_ns=0,lazy_reverse_ns=0,total_run_ns=0,release_ns=0;
 std::uint64_t calls=0,fallback_calls=0,guard_calls=0,old_reads=0,future_skips=0,outside_skips=0;
};
using Snapshot=bool(*)(rcc_api::Module*,Phases*);
}
