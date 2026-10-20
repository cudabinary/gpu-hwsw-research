#include "rcc/v1.hpp"
#include "adapter.hpp"
#include <chrono>
#include <new>
#ifndef RCC_KIND
#define RCC_KIND 1
#endif
namespace rcc_api {
using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t){return std::chrono::duration<double,std::nano>(Clock::now()-t).count();}
class CpuModule final:public Module {
 GraphPtr graph_;Options options_;std::shared_ptr<const independent::Graph> legacy_;
 std::unique_ptr<merged::Executor> engine_,fallback_;
 std::unique_ptr<consumer::Workspace> workspace_;
 bool valid(const GraphPtr&g)const noexcept {return graph_&&g&&g.get()==graph_.get()&&g->identity==graph_->identity&&g->version==graph_->version;}
 Reply execute(const Request&q){
  Reply out;auto start=Clock::now();
  if(!engine_)out.status=Status::NOT_PREPARED;
  else if(!valid(q.graph))out.status=Status::INVALID_GRAPH;
  else if(q.source>=graph_->n)out.status=Status::INVALID_SOURCE;
  else if(q.cancelled)out.status=Status::CANCELLED;
  else try {
   bool active=options_.enabled&&q.enabled&&RCC_KIND!=0;
   auto& e=active?*engine_:*fallback_;
   out.metrics.certificate_applied=active&&can_apply(q.graph,q.source);
   // Reserve public output before the legacy executor may update certificates.
   // A return-allocation failure therefore leaves certificate state unchanged.
   if(q.fail_output_allocation)throw std::bad_alloc();
   auto prepared=std::shared_ptr<Output>(new Output(graph_,q.source));
   auto pair=e.run<true>(q.source,*workspace_,q.row_budget,false);
   if(!pair.first){out.status=Status::CANCELLED;}
   else {
    // No allocations after legacy certificate publication. Readers only receive const ownership.
    std::copy(pair.first->distance().begin(),pair.first->distance().end(),prepared->distance_.begin());
    out.output=std::move(prepared);
    out.status=Status::OK;
   }
   out.metrics.inspected_edges=pair.second.edges;
   out.metrics.fallback=(!active||e.fallback||!out.metrics.certificate_applied);
   out.metrics.cache_bytes=engine_->cache_bytes();
   out.metrics.adapter_csr_bytes=legacy_->payload_bytes();
   out.metrics.output_copy_elements=out.output?graph_->n:0;
  }catch(const std::bad_alloc&){out.status=Status::ALLOCATION_FAILED;out.output.reset();}
   catch(...){out.status=Status::INTERNAL_ERROR;out.output.reset();}
  out.metrics.run_ns=elapsed(start);return out;
 }
public:
 Capabilities capabilities()const noexcept override{return {API_VERSION,RCC_KIND==0?"baseline-1":RCC_KIND==1?"rcc-table-20261021-v1":"rcc-last-20261021-v1",true,false};}
 Reply prepare(GraphPtr g,const Options&o,std::int64_t seed)override{
  release();Reply out;auto start=Clock::now();
  if(o.backend!=Backend::CPU){out.status=Status::UNSUPPORTED_BACKEND;return out;}
  if(!g){out.status=Status::INVALID_GRAPH;return out;}
  try{
   graph_=std::move(g);options_=o;
   std::vector<std::pair<U,U>>edges;edges.reserve(graph_->col.size());
   for(U u=0;u<graph_->n;++u)for(L p=graph_->row[u];p<graph_->row[u+1];++p)edges.emplace_back(u,graph_->col[p]);
   legacy_=std::make_shared<const independent::Graph>(graph_->n,graph_->version,edges);
   engine_=std::make_unique<merged::Executor>(legacy_,nullptr,merged::mode(RCC_KIND==0?"PUSH_N":RCC_KIND==1?"PUSH_RCC_TABLE":"PUSH_RCC_LAST"),o.cache_limit,o.fail_cache_allocation);
   fallback_=std::make_unique<merged::Executor>(legacy_,nullptr,merged::mode("PUSH_N"));
   workspace_=std::make_unique<consumer::Workspace>(graph_->n);
   out.status=Status::OK;
   if(seed>=0){Request q{graph_,U(seed)};if(std::uint64_t(seed)>=graph_->n)out.status=Status::INVALID_SOURCE;else out=execute(q);}
  }catch(const std::bad_alloc&){release();out.status=Status::ALLOCATION_FAILED;}
   catch(...){release();out.status=Status::INTERNAL_ERROR;}
  out.metrics.prepare_ns=elapsed(start);return out;
 }
 bool can_apply(const GraphPtr&g,U s)const noexcept override{return RCC_KIND!=0&&options_.enabled&&valid(g)&&engine_&&!engine_->fallback&&s<g->n&&engine_->bound(s)<g->n;}
 Reply run(const Request&q)override{return execute(q);}
 Reply update(const Request&q)override{auto out=execute(q);out.metrics.update_ns=out.metrics.run_ns;return out;}
 void invalidate()noexcept override{if(engine_)engine_->reset();}
 void release()noexcept override{engine_.reset();fallback_.reset();workspace_.reset();legacy_.reset();graph_.reset();}
};
}
extern "C" rcc_api::Module* rcc_create(unsigned v){if(v!=rcc_api::API_VERSION)return nullptr;try{return new rcc_api::CpuModule;}catch(...){return nullptr;}}
extern "C" void rcc_destroy(rcc_api::Module*p){delete p;}
