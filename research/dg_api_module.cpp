#include "rcc/v1.hpp"
#include "dg_api_audit.hpp"
#include "dg_api_kernel.hpp"
#include <chrono>
#include <new>
namespace rcc_api {
using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t){return std::chrono::duration<double,std::nano>(Clock::now()-t).count();}
// Policy 0/1/2: matched Push/Table/Last; 3/4/5: P2/RIE/RIE+Table controls;
// 6/7/8/9: Distance COUNT/CLOSURE/RADIUS/FRONTIER; 10: exact last-result reuse.
class CpuModule final:public Module {
 unsigned policy_;bool deferred_,phase_enabled_,first_=true,cache_ok_=false,reverse_failed_=false;
 GraphPtr graph_;Options options_;
 std::shared_ptr<const independent::Graph> legacy_;
 std::shared_ptr<const independent::Reverse> reverse_;
 std::unique_ptr<consumer::Workspace> workspace_;
 std::vector<U> table_;Result previous_;U reached_=0;
 dg_audit::Phases phases_;
 bool cached()const{return policy_==1||policy_==2||policy_==5||policy_>=6;}
 bool valid(const GraphPtr&g)const noexcept{return graph_&&g&&g.get()==graph_.get()&&g->identity==graph_->identity&&g->version==graph_->version;}
 bool needs_reverse()const{return policy_>=3&&policy_<=9;}
 L cache_bytes()const{return 4ULL*table_.capacity()+(previous_?4ULL*graph_->n:0);}
 U bound(U s)const noexcept{
  if(!table_.empty())return table_[s];
  return previous_&&previous_->distance()[s]>=0?reached_:graph_->n;
 }
 bool ensure_reverse(){
  if(reverse_)return true;if(reverse_failed_)return false;
  try{auto a=std::make_shared<independent::Account>(32ULL<<20);independent::Builder b(legacy_,a);b.finish();reverse_=b.take();return true;}
  catch(const std::bad_alloc&){reverse_failed_=true;return false;}
 }
 Reply execute(const Request&q){
  Reply out;auto start=Clock::now();dg_audit::Phases p;p.enabled=phase_enabled_;p.exact_edge_counter=policy_!=3;
  phases_.allocation_ns=phases_.algorithm_ns=phases_.copy_ns=phases_.maintenance_ns=phases_.lazy_reverse_ns=0;
  if(!workspace_)out.status=Status::NOT_PREPARED;
  else if(!valid(q.graph))out.status=Status::INVALID_GRAPH;
  else if(q.source>=graph_->n)out.status=Status::INVALID_SOURCE;
  else if(q.cancelled)out.status=Status::CANCELLED;
  else try{
   const bool enabled=options_.enabled&&q.enabled;
   const bool finite=q.row_budget!=std::numeric_limits<L>::max();
   const bool applicable=can_apply(q.graph,q.source);
   if(q.fail_output_allocation)throw std::bad_alloc();
   if(policy_==10&&enabled&&cache_ok_&&previous_&&previous_->source()==q.source&&!finite){
    out.output=previous_;out.status=Status::OK;out.metrics.fallback=false;
   }else{
    auto mark=phase_enabled_?Clock::now():Clock::time_point{};
    auto prepared=std::shared_ptr<Output>(new Output(graph_,q.source));
    if(phase_enabled_)p.allocation_ns=elapsed(mark);
    bool direction=enabled&&!finite&&!first_&&((policy_==3||policy_==4)||(policy_==5&&cache_ok_)||(policy_>=6&&policy_<=9&&cache_ok_&&applicable));
    if(direction){mark=phase_enabled_?Clock::now():Clock::time_point{};direction=ensure_reverse();if(phase_enabled_)p.lazy_reverse_ns=elapsed(mark);}
    mark=phase_enabled_?Clock::now():Clock::time_point{};
    dg_kernel::Work st;const U before=cached()&&cache_ok_?bound(q.source):graph_->n;
    if(direction&&policy_>=6){st=dg_kernel::run(*legacy_,*reverse_,q.source,*workspace_,previous_->distance(),before,policy_-6);}
    else if(direction&&policy_==3){
     // Frozen original P2, without diagnostic vector allocation in its timing.
     consumer::function(consumer::Mode::DIRECTION)(*legacy_,reverse_.get(),q.source,*workspace_);st.complete=true;
    }else if(direction){static_cast<stop_bridge::Work&>(st)=stop_bridge::direction<true>(*legacy_,*reverse_,q.source,*workspace_,stop_bridge::N|stop_bridge::RIE|(policy_==5?stop_bridge::RCC:0),policy_==5?before:graph_->n);}
    else{
     const bool push_cert=enabled&&cache_ok_&&(policy_==1||policy_==2)&&applicable&&!finite;
     static_cast<stop_bridge::Work&>(st)=stop_bridge::push<true>(*legacy_,q.source,*workspace_,push_cert?before:graph_->n,true,q.row_budget);
    }
    if(phase_enabled_)p.algorithm_ns=elapsed(mark);
    out.metrics.inspected_edges=st.edges;
    out.metrics.certificate_applied=enabled&&applicable&&!finite&&(direction||(policy_==1||policy_==2));
    out.metrics.fallback=!(direction||(enabled&&cache_ok_&&(policy_==1||policy_==2)&&applicable&&!finite));
    if(!st.complete)out.status=Status::CANCELLED;
    else{
     mark=phase_enabled_?Clock::now():Clock::time_point{};
     std::copy(workspace_->base.distance.begin(),workspace_->base.distance.end(),prepared->distance_.begin());
     if(phase_enabled_)p.copy_ns=elapsed(mark);
     // Publication is non-allocating after the successful owned result copy.
     mark=phase_enabled_?Clock::now():Clock::time_point{};
     if(enabled&&cache_ok_){
      if(!table_.empty()){if(st.seen<before)for(U v=0;v<graph_->n;++v)if(prepared->distance_[v]>=0&&table_[v]>st.seen)table_[v]=st.seen;}
      else if(policy_==2||policy_>=6){previous_=prepared;reached_=st.seen;}
     }
     first_=false;out.output=std::move(prepared);out.status=Status::OK;out.metrics.output_copy_elements=graph_->n;
     if(phase_enabled_)p.maintenance_ns=elapsed(mark);
    }
    p.old_reads=st.old_reads;p.future_skips=st.future_skips;p.outside_skips=st.outside_skips;
    phases_.fallback_calls+=out.metrics.fallback;phases_.guard_calls+=direction&&policy_>=6;
   }
  }catch(const std::bad_alloc&){out.status=Status::ALLOCATION_FAILED;out.output.reset();}
   catch(...){out.status=Status::INTERNAL_ERROR;out.output.reset();}
  if(legacy_)out.metrics.adapter_csr_bytes=legacy_->payload_bytes();
  if(graph_)out.metrics.cache_bytes=cache_bytes();
  out.metrics.run_ns=elapsed(start);p.total_run_ns=out.metrics.run_ns;
  phases_.enabled=p.enabled;phases_.exact_edge_counter=p.exact_edge_counter;
  phases_.allocation_ns=p.allocation_ns;phases_.algorithm_ns=p.algorithm_ns;phases_.copy_ns=p.copy_ns;phases_.maintenance_ns=p.maintenance_ns;phases_.lazy_reverse_ns=p.lazy_reverse_ns;phases_.total_run_ns=p.total_run_ns;
  phases_.old_reads=p.old_reads;phases_.future_skips=p.future_skips;phases_.outside_skips=p.outside_skips;++phases_.calls;
  return out;
 }
public:
 CpuModule(unsigned p,bool deferred,bool timers):policy_(p),deferred_(deferred),phase_enabled_(timers){}
 Capabilities capabilities()const noexcept override{
  static const char*names[]={"baseline-1","matched-table-api1","matched-last-api1","old-p2-comparator-api1","rie-comparator-api1","rie-table-comparator-api1","distance-count-api1-experimental","distance-closure-api1-experimental","distance-radius-api1-experimental","distance-frontier-api1-experimental","exact-reuse-comparator-api1"};
  return {API_VERSION,names[policy_],true,false};
 }
 Reply prepare(GraphPtr g,const Options&o,std::int64_t seed)override{
  release();phases_={};phases_.enabled=phase_enabled_;phases_.exact_edge_counter=policy_!=3;auto start=Clock::now();Reply out;
  if(o.backend!=Backend::CPU)out.status=Status::UNSUPPORTED_BACKEND;
  else if(!g)out.status=Status::INVALID_GRAPH;
  else try{
   graph_=std::move(g);options_=o;auto mark=phase_enabled_?Clock::now():Clock::time_point{};
   std::vector<std::pair<U,U>>edges;edges.reserve(graph_->col.size());
   for(U u=0;u<graph_->n;++u)for(L e=graph_->row[u];e<graph_->row[u+1];++e)edges.emplace_back(u,graph_->col[e]);
   legacy_=std::make_shared<const independent::Graph>(graph_->n,graph_->version,edges);
   if(phase_enabled_)phases_.prepare_graph_ns=elapsed(mark);
   mark=phase_enabled_?Clock::now():Clock::time_point{};
   workspace_=std::make_unique<consumer::Workspace>(graph_->n,needs_reverse());
   cache_ok_=cached()&&o.enabled&&!o.fail_cache_allocation&&o.cache_limit>=4ULL*graph_->n;
   if(cache_ok_&&(policy_==1||policy_==5))try{table_.assign(graph_->n,graph_->n);}catch(const std::bad_alloc&){cache_ok_=false;table_.clear();}
   if(phase_enabled_)phases_.prepare_workspace_ns=elapsed(mark);
   if(needs_reverse()&&!deferred_&&o.enabled&&(!cached()||cache_ok_)){
    mark=phase_enabled_?Clock::now():Clock::time_point{};ensure_reverse();if(phase_enabled_)phases_.prepare_reverse_ns=elapsed(mark);
   }
   out.status=Status::OK;
   if(seed>=0){if(std::uint64_t(seed)>=graph_->n)out.status=Status::INVALID_SOURCE;else out=execute({graph_,U(seed)});}
  }catch(const std::bad_alloc&){release();out.status=Status::ALLOCATION_FAILED;}
   catch(...){release();out.status=Status::INTERNAL_ERROR;}
  out.metrics.prepare_ns=elapsed(start);return out;
 }
 bool can_apply(const GraphPtr&g,U s)const noexcept override{
  return options_.enabled&&cache_ok_&&!reverse_failed_&&valid(g)&&s<g->n&&policy_!=10&&bound(s)<g->n;
 }
 Reply run(const Request&q)override{return execute(q);}
 Reply update(const Request&q)override{auto out=execute(q);out.metrics.update_ns=out.metrics.run_ns;return out;}
 void invalidate()noexcept override{previous_.reset();reached_=0;std::fill(table_.begin(),table_.end(),graph_?graph_->n:0);}
 void release()noexcept override{
  auto start=phase_enabled_?Clock::now():Clock::time_point{};
  previous_.reset();std::vector<U>().swap(table_);workspace_.reset();reverse_.reset();legacy_.reset();graph_.reset();
  reached_=0;first_=true;cache_ok_=reverse_failed_=false;
  if(phase_enabled_)phases_.release_ns=elapsed(start);
 }
 dg_audit::Phases snapshot()const{return phases_;}
};
Module* make_experimental(unsigned p,bool deferred,bool timers){if(p>10)return nullptr;try{return new CpuModule(p,deferred,timers);}catch(...){return nullptr;}}
}
extern "C" bool dg_audit_snapshot(rcc_api::Module*m,dg_audit::Phases*out){if(!m||!out)return false;*out=static_cast<rcc_api::CpuModule*>(m)->snapshot();return true;}
