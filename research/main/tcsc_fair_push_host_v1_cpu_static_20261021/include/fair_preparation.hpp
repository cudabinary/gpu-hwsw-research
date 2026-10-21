#pragma once
#include "independent_builder.hpp"
#include <chrono>

// Exact indegree-presence metadata, not a reverse adjacency/index.
namespace fair {
using independent::Graph;using independent::Account;using independent::Buffer;
using independent::U;using independent::L;using independent::require;
class CsrIncomingBound {
    std::shared_ptr<const Graph> graph_;
    Buffer<L> present_;U positive_=0;L version_=0;bool ready_=false;
public:
    static CsrIncomingBound prepare(std::shared_ptr<const Graph> g,std::shared_ptr<Account> account,
                                   const std::atomic<bool>*cancel=nullptr){
        require(g&&g->n()&&g->version(),"metadata graph");
        if(cancel&&cancel->load(std::memory_order_acquire))throw std::runtime_error("metadata cancelled");
        CsrIncomingBound out;out.graph_=g;out.version_=g->version();
        out.present_=Buffer<L>(account,(L(g->n())+63)/64,true);
        for(L e=0;e<g->m();++e){
            if((e%4096)==0&&cancel&&cancel->load(std::memory_order_acquire))throw std::runtime_error("metadata cancelled");
            U v=g->col()[e];require(v<g->n(),"metadata destination");L mask=L(1)<<(v%64);
            if(!(out.present_[v/64]&mask)){out.present_[v/64]|=mask;++out.positive_;}
        }
        if(cancel&&cancel->load(std::memory_order_acquire))throw std::runtime_error("metadata cancelled");
        out.ready_=true;return out;
    }
    bool can_apply(const Graph&g)const{return ready_&&graph_&&graph_.get()==&g&&version_==g.version()&&graph_->n()==g.n()&&graph_->m()==g.m();}
    U limit(const Graph&g,U source)const{
        require(source<g.n(),"metadata source");
        if(!can_apply(g))return g.n(); // Exact EARLY_N fallback; never use stale bits.
        return positive_+U(!(present_[source/64]&(L(1)<<(source%64))));
    }
    U positive_vertices()const{return positive_;}
    L payload_bytes()const{return L(present_.size())*sizeof(L);}
};
struct Prepared {
    std::shared_ptr<const Graph> graph;
    std::shared_ptr<Account> account;
    std::shared_ptr<const independent::Reverse> reverse;
    CsrIncomingBound bound;
    double total_ms=0,reverse_ms=0,metadata_ms=0;
};
inline Prepared prepare(std::shared_ptr<const Graph>g,U mode,std::shared_ptr<Account>account,
                        const std::atomic<bool>*cancel=nullptr){
    require(mode==5||mode==7,"fair modes only");auto start=std::chrono::steady_clock::now();
    Prepared p;p.graph=g;p.account=account;
    if(mode==7){auto t=std::chrono::steady_clock::now();p.bound=CsrIncomingBound::prepare(g,account,cancel);
        p.metadata_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count();}
    else {auto t=std::chrono::steady_clock::now();
        if(cancel&&cancel->load(std::memory_order_acquire))throw std::runtime_error("reverse cancelled");
        {independent::Builder builder(g,account);builder.finish();
         if(cancel&&cancel->load(std::memory_order_acquire))throw std::runtime_error("reverse cancelled");p.reverse=builder.take();}
        p.reverse_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count();}
    p.total_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();return p;
}
inline L projected_device_bytes(const Graph&g,U mode){
    require(mode==5||mode==7,"fair modes only");
    L original=8*(L(g.n())+1)+4*std::max<L>(1,g.m());
    L common=original+12*L(g.n())+28;
    return common+(mode==5?8*(L(g.n())+1)+4*std::max<L>(1,g.m())+8*((L(g.n())+63)/64):0);
}
} // namespace fair
