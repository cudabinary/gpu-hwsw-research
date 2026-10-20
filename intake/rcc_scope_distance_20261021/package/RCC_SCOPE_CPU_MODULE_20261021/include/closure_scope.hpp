#pragma once
// RCC-Scope v0.1. CPU single-owner reference, not concurrent CUDA code.
// Scope is learned only from a completed BFS. No input/future-oracle access.
#include "stop_bridge.hpp"
#include <numeric>
#include <memory>
namespace rcc_scope {
using namespace independent;
struct Work {
    L edges=0, vertex_tests=0, levels=0, bitmap_clear=0, bitmap_set=0;
    L publish_tests=0,publish_writes=0,cache_live_bytes=0,cache_peak_bytes=0;
    L remaining_global=0, remaining_scope=0;
    U seen=0, domain_size=0, stop_reason=0;
    bool complete=false, hit=false, published=false, allocation_refused=false;
};
// This descriptor is a borrowed view. Membership/list lifetime is owner-bound.
struct Domain { const std::vector<U>* list=nullptr; L incoming=0; U size=0; };
struct Options { bool compact=false, scoped_policy=false, scoped_stop=false; };

// Safe even with outside->inside edges: sum GLOBAL indegree over vertices in D.
// Not sum(outdegree[D])-sum(global indegree[seen]); the latter may underflow.
template<bool Diagnose>
SB_NOINLINE Work direction(const Graph&g,const Reverse&r,U s,consumer::Workspace&w,
        Domain domain,Options opt,std::vector<U>&pending,
        L max_levels=std::numeric_limits<L>::max()){
    require(r.graph_ptr().get()==&g,"reverse identity mismatch");
    require(g.n()>0&&g.n()<=U(std::numeric_limits<int>::max())&&s<g.n(),"source/size range");
    require(w.base.distance.size()==g.n()&&w.base.queue.size()==g.n()&&w.next.size()==g.n(),"workspace mismatch");
    require(domain.size>0&&domain.size<=g.n(),"invalid domain size");
    auto&d=w.base.distance;std::fill(d.begin(),d.end(),-1);d[s]=0;
    auto*front=&w.base.queue;auto*next=&w.next;(*front)[0]=s;
    const L source_in=r.row()[s+1]-r.row()[s];
    require(source_in<=domain.incoming,"scope indegree underflow");
    L rem_global=g.m()-source_in,rem_scope=domain.incoming-source_in;
    U seen=1,depth=0;L nf=1,fe=g.row()[s+1]-g.row()[s];bool pull=false;
    Work st;st.domain_size=domain.size;
    if(opt.compact){pending.clear();if(domain.list)pending.assign(domain.list->begin(),domain.list->end());
      else{pending.resize(g.n());std::iota(pending.begin(),pending.end(),0u);}}
    while(nf){
        require(seen<=domain.size,"unsafe closure cardinality");
        if(seen==domain.size){st.stop_reason=(domain.size==g.n()?1:3);break;}
        if(rem_global==0){st.stop_reason=2;break;}
        if(opt.scoped_stop&&rem_scope==0){st.stop_reason=4;break;}
        if(depth>=max_levels){st.seen=seen;st.remaining_global=rem_global;st.remaining_scope=rem_scope;return st;}
        const U policy_n=opt.scoped_policy?domain.size:g.n();
        const L policy_m=opt.scoped_policy?rem_scope:rem_global;
        if(pull){if(nf<std::max<L>(1,policy_n/consumer::BETA))pull=false;}
        else if(fe>policy_m/consumer::ALPHA)pull=true;
        if(pull){std::fill(w.bitmap.begin(),w.bitmap.end(),0);
            for(L i=0;i<nf;++i){U u=(*front)[i];w.bitmap[u/64]|=L(1)<<(u%64);}
            if constexpr(Diagnose){st.bitmap_clear+=w.bitmap.size();st.bitmap_set+=nf;}}
        L found=0,next_edges=0;
        auto discover=[&](U v){d[v]=int(depth)+1;(*next)[found++]=v;next_edges+=g.row()[v+1]-g.row()[v];
            const L k=r.row()[v+1]-r.row()[v];
            require(k<=rem_global&&k<=rem_scope,"remaining counter underflow");
            rem_global-=k;rem_scope-=k;++seen;};
        if(pull){
            auto visit=[&](U v){if constexpr(Diagnose)++st.vertex_tests;
                if(d[v]>=0)return;
                for(L e=r.row()[v];e<r.row()[v+1];++e){if constexpr(Diagnose)++st.edges;
                    U u=r.source()[e];if((w.bitmap[u/64]>>(u%64))&1u){discover(v);break;}}};
            if(opt.compact){L keep=0;for(U v:pending){visit(v);if(d[v]<0)pending[keep++]=v;}pending.resize(keep);}
            else if(domain.list){for(U v:*domain.list)visit(v);}
            else{for(U v=0;v<g.n();++v)visit(v);}
        }else{
            for(L i=0;i<nf;++i){U u=(*front)[i];for(L e=g.row()[u];e<g.row()[u+1];++e){
                if constexpr(Diagnose){++st.edges;}U v=g.col()[e];if(d[v]<0)discover(v);}}
        }
        nf=found;fe=next_edges;std::swap(front,next);++depth;
        if constexpr(Diagnose)++st.levels;
    }
    require(seen<=domain.size,"unsafe domain");st.seen=seen;st.complete=true;
    st.remaining_global=rem_global;st.remaining_scope=rem_scope;return st;
}

// A published certificate is immutable and graph-object bound.
// The caller cannot submit an arbitrary partial BFS as a certificate.
class Closure {
    friend class Executor;
    std::shared_ptr<const Graph> graph_;
    std::vector<U> vertices_;
    std::vector<L> bits_;
    L incoming_=0;
public:
    bool contains(U s)const{return s<graph_->n()&&((bits_[s/64]>>(s%64))&1u);}
    U size()const{return U(vertices_.size());}
    L bytes()const{return sizeof(U)*L(vertices_.capacity())+sizeof(L)*L(bits_.capacity());}
    const std::vector<U>&vertices()const{return vertices_;}
    L incoming()const{return incoming_;}
    const Graph*identity()const{return graph_.get();}
};
enum class Kind {COUNT_ONLY,SCOPE_GLOBAL,SCOPE_LOCAL,SCOPE_LOCAL_COMPACT,DO_COMPACT};
class Executor {
    std::shared_ptr<const Graph>g_;std::shared_ptr<const Reverse>r_;Kind kind_;
    std::shared_ptr<const Closure>closure_;std::vector<U>pending_;
    L memory_limit_,last_peak_=0;bool fail_next_=false;
public:
    Executor(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,Kind kind,
             L memory_limit=std::numeric_limits<L>::max()):g_(std::move(g)),r_(std::move(r)),kind_(kind),memory_limit_(memory_limit){
        require(g_&&r_&&g_.get()==r_->graph_ptr().get()&&g_->n()>0,"graph binding");}
    void reset(){closure_.reset();pending_.clear();last_peak_=0;}
    void fail_next_publication(){fail_next_=true;}
    auto snapshot()const{return closure_;}
    L bytes()const{return (closure_?closure_->bytes():0)+sizeof(U)*L(pending_.capacity());}
    L peak_bytes()const{return std::max(last_peak_,bytes());}
    template<bool Diagnose=false> Work run(U s,consumer::Workspace&w,L max_levels=std::numeric_limits<L>::max()){
        require(s<g_->n(),"source range");
        const bool enabled=kind_!=Kind::DO_COMPACT;
        const bool hit=enabled&&closure_&&closure_->contains(s);
        const auto old=closure_;
        Domain domain{nullptr,g_->m(),g_->n()};
        Options opt;
        if(hit){domain.size=closure_->size();
            // COUNT_ONLY preserves original global policy, scans and global RIE.
            // It has exactly the same closure storage/update cost as SCOPE_GLOBAL.
            if(kind_!=Kind::COUNT_ONLY){domain.list=&closure_->vertices_;domain.incoming=closure_->incoming_;}}
        if(kind_==Kind::COUNT_ONLY)domain.incoming=g_->m();
        opt.scoped_policy=kind_==Kind::SCOPE_LOCAL||kind_==Kind::SCOPE_LOCAL_COMPACT;
        opt.scoped_stop=opt.scoped_policy;
        opt.compact=kind_==Kind::SCOPE_LOCAL_COMPACT||kind_==Kind::DO_COMPACT;
        Work st=direction<Diagnose>(*g_,*r_,s,w,domain,opt,pending_,max_levels);st.hit=hit;
        if(st.complete&&enabled&&st.seen<g_->n()&&(!hit||st.seen<closure_->size())){
            const L need=L(st.seen)*sizeof(U)+((L(g_->n())+63)/64)*sizeof(L);
            const L oldbytes=closure_?closure_->bytes():0;
            const L scratch=L(pending_.capacity())*sizeof(U);
            if(need>memory_limit_||oldbytes+scratch>memory_limit_-need){st.allocation_refused=true;}
            else try{
                if(fail_next_){fail_next_=false;throw std::bad_alloc();}
                auto c=std::make_shared<Closure>();c->graph_=g_;c->vertices_.reserve(st.seen);c->bits_.assign((L(g_->n())+63)/64,0);
                for(U v=0;v<g_->n();++v){if constexpr(Diagnose)++st.publish_tests;
                    if(w.base.distance[v]>=0){c->vertices_.push_back(v);c->bits_[v/64]|=L(1)<<(v%64);
                        c->incoming_+=r_->row()[v+1]-r_->row()[v];if constexpr(Diagnose)++st.publish_writes;}}
                require(c->size()==st.seen,"complete output cardinality");
                require(c->incoming_<=g_->m(),"scope indegree bound");
                const L real=oldbytes+scratch+c->bytes();
                if(real>memory_limit_){st.allocation_refused=true;}
                else{last_peak_=std::max(last_peak_,real);closure_=std::move(c);st.published=true;}
            }catch(const std::bad_alloc&){st.allocation_refused=true;}
        }
        // A full-domain complete result is unnecessary; old certificate remains valid.
        // Aborts never publish. Output remains in w.base.distance (borrow until next run).
        st.cache_live_bytes=bytes();st.cache_peak_bytes=peak_bytes();return st;
    }
};

// Conventional weakly-connected-component scope baseline. Preparation is charged.
class WeakComponents {
    std::shared_ptr<const Graph>g_;
    std::vector<U>id_;std::vector<std::vector<U>>lists_;std::vector<L>mass_;
public:
    explicit WeakComponents(std::shared_ptr<const Graph>g):g_(std::move(g)){
        require(bool(g_),"WCC binding");
        id_.resize(g_->n());std::iota(id_.begin(),id_.end(),0u);std::vector<U>sz(g_->n(),1);
        auto root=[&](U v){while(v!=id_[v]){id_[v]=id_[id_[v]];v=id_[v];}return v;};
        for(U u=0;u<g_->n();++u)for(L e=g_->row()[u];e<g_->row()[u+1];++e){U a=root(u),b=root(g_->col()[e]);if(a==b)continue;
            if(sz[a]<sz[b]){std::swap(a,b);}id_[b]=a;sz[a]+=sz[b];}
        std::vector<U>map(g_->n(),std::numeric_limits<U>::max());
        for(U v=0;v<g_->n();++v){U a=root(v);if(map[a]==std::numeric_limits<U>::max()){map[a]=U(lists_.size());lists_.emplace_back();mass_.push_back(0);}}
        for(U v=0;v<g_->n();++v){U c=map[root(v)];sz[v]=c;lists_[c].push_back(v);mass_[c]+=g_->row()[v+1]-g_->row()[v];}id_.swap(sz);
    }
    U components()const{return U(lists_.size());}
    L bytes()const{L s=4*L(id_.capacity())+8*L(mass_.capacity());for(auto&l:lists_)s+=4*L(l.capacity());return s;}
    Domain view(U s)const{require(s<g_->n(),"WCC source");U c=id_[s];return {&lists_[c],mass_[c],U(lists_[c].size())};}
};
} // namespace rcc_scope
