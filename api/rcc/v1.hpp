#pragma once
#include <cstdint>
#include <memory>
#include <string>
#include <utility>
#include <vector>
#include <limits>
namespace rcc_api {
constexpr unsigned API_VERSION=0x00010000;
using U=std::uint32_t; using L=std::uint64_t;
enum class Backend {CPU, CUDA};
enum class Status {OK,CANCELLED,ALLOCATION_FAILED,INVALID_GRAPH,INVALID_SOURCE,NOT_PREPARED,UNSUPPORTED_BACKEND,INTERNAL_ERROR};
struct Graph final {
 const std::string identity; const L version; const U n;
 const std::vector<L> row; const std::vector<U> col;
 Graph(std::string id,L v,U n_,std::vector<L> r,std::vector<U> c);
 static std::shared_ptr<const Graph> from_edges(std::string,L,U,const std::vector<std::pair<U,U>>&);
};
using GraphPtr=std::shared_ptr<const Graph>;
class Output final {
 friend class CpuModule;
 GraphPtr graph_;U source_;std::vector<int> distance_;
 Output(GraphPtr g,U s):graph_(std::move(g)),source_(s),distance_(graph_->n){}
public:
 const GraphPtr& graph()const noexcept{return graph_;}
 U source()const noexcept{return source_;}
 const std::vector<int>& distance()const noexcept{return distance_;}
};
using Result=std::shared_ptr<const Output>;
struct Metrics {
 double prepare_ns=0,run_ns=0,update_ns=0;
 L inspected_edges=0,cache_bytes=0,adapter_csr_bytes=0,output_copy_elements=0;
 bool fallback=false,certificate_applied=false;
};
struct Options {Backend backend=Backend::CPU;bool enabled=true;L cache_limit=32ULL<<20;bool fail_cache_allocation=false;};
struct Request {GraphPtr graph;U source=0;bool enabled=true;bool cancelled=false;L row_budget=std::numeric_limits<L>::max();bool fail_output_allocation=false;};
struct Reply {Status status=Status::NOT_PREPARED;Result output;Metrics metrics;};
struct Capabilities {unsigned api_version;const char*implementation;bool cpu;bool cuda;};
// One owner serializes all Module calls. Published outputs are immutable and
// independent of module lifetime. No certificate import from untrusted arrays.
class Module {
public:
 virtual ~Module()=default;
 virtual Capabilities capabilities()const noexcept=0;
 virtual Reply prepare(GraphPtr,const Options&,std::int64_t seed_source=-1)=0;
 virtual bool can_apply(const GraphPtr&,U)const noexcept=0;
 virtual Reply run(const Request&)=0;
 // Computes a completed BFS for source and updates the certificate atomically.
 // Its full compute/copy/publication cost is reported; it is not free ingestion.
 virtual Reply update(const Request&)=0;
 virtual void invalidate()noexcept=0;
 virtual void release()noexcept=0;
};
using Create=Module*(*)(unsigned);using Destroy=void(*)(Module*);
}
extern "C" rcc_api::Module* rcc_create(unsigned);
extern "C" void rcc_destroy(rcc_api::Module*);
