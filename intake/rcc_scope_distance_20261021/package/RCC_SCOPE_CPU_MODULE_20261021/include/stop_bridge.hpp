#pragma once
// Independent CPU integration probe, 2026-10-21. Not GPU code.
// Uses the supplied Codex graph/reverse and the exact alpha=15,beta=24 policy.
// No new builder, no future-source knowledge, immutable graph identity.
#include "consumers.hpp"
#include <limits>
#include <cstddef>

namespace stop_bridge {
using namespace independent;
#if defined(__GNUC__) && !defined(__clang__)
#define SB_NOINLINE __attribute__((noinline,noclone))
#else
#define SB_NOINLINE
#endif
struct Work {
    L edges=0, vertex_tests=0, levels=0, bitmap_clear=0, bitmap_set=0;
    U seen=0, limit=0;
    L remaining_in=0, publish_visits=0, publish_writes=0;
    bool complete=false;
    unsigned reason=0; // 0 exhausted, 1 n, 2 remaining indegree zero, 3 historical RCC
};
enum StopFlag : unsigned {N=1, RIE=2, RCC=4};
// remaining is SUM indegree(v) over undiscovered v, not an estimate.
// If it is zero, no undiscovered v can be reached by any edge. Safe for exact
// unweighted full-distance BFS, NOT edge callbacks or shortest-path counts.
template<bool Diagnose>
SB_NOINLINE Work direction(const Graph&g,const Reverse&r,U s,
              consumer::Workspace&w,unsigned flags,U upper,
              L max_levels=std::numeric_limits<L>::max()) {
    require(r.graph_ptr().get()==&g,"reverse graph identity mismatch");
    require(s<g.n()&&upper>0&&upper<=g.n(),"invalid source/bound");
    require(w.base.distance.size()==g.n()&&w.base.queue.size()==g.n()&&
            w.next.size()==g.n()&&w.bitmap.size()==(L(g.n())+63)/64,"workspace mismatch");
    auto &dist=w.base.distance;
    std::fill(dist.begin(),dist.end(),-1); dist[s]=0;
    auto*front=&w.base.queue;auto*next=&w.next;(*front)[0]=s;
    L nf=1,fe=g.row()[s+1]-g.row()[s];
    L remaining=g.m()-(r.row()[s+1]-r.row()[s]);
    bool pull=false;U depth=0,seen=1;Work st;st.limit=upper;
    while(nf){
        require(seen<=upper,"invalid historical upper bound");
        if((flags&N)&&seen==g.n()){st.reason=1;break;}
        if((flags&RIE)&&remaining==0){st.reason=2;break;}
        if((flags&RCC)&&seen==upper){st.reason=3;break;}
        if(depth>=max_levels){st.seen=seen;st.remaining_in=remaining;return st;}
        if(pull){if(nf<std::max<L>(1,g.n()/consumer::BETA))pull=false;}
        else if(fe>remaining/consumer::ALPHA)pull=true;
        if(pull){std::fill(w.bitmap.begin(),w.bitmap.end(),0);
            for(L i=0;i<nf;++i){U u=(*front)[i];w.bitmap[u/64]|=L(1)<<(u%64);}
            if constexpr(Diagnose){st.bitmap_clear+=w.bitmap.size();st.bitmap_set+=nf;}}
        L found=0,next_edges=0;
        auto discover=[&](U v){dist[v]=int(depth)+1;(*next)[found++]=v;
            next_edges+=g.row()[v+1]-g.row()[v];
            L indegree=r.row()[v+1]-r.row()[v];require(indegree<=remaining,"remaining underflow");
            remaining-=indegree;++seen;};
        if(pull){
            for(U v=0;v<g.n();++v){if constexpr(Diagnose)++st.vertex_tests;
                if(dist[v]>=0)continue;
                for(L p=r.row()[v];p<r.row()[v+1];++p){if constexpr(Diagnose)++st.edges;
                    U u=r.source()[p];if((w.bitmap[u/64]>>(u%64))&1){discover(v);break;}}}
        }else{
            for(L i=0;i<nf;++i){U u=(*front)[i];
                for(L e=g.row()[u];e<g.row()[u+1];++e){if constexpr(Diagnose)++st.edges;
                    U v=g.col()[e];if(dist[v]<0)discover(v);}}
        }
        nf=found;fe=next_edges;std::swap(front,next);++depth;
        if constexpr(Diagnose)++st.levels;
        require(depth<=L(g.n())+1,"BFS level limit");
    }
    require(seen<=upper,"invalid historical bound");
    st.seen=seen;st.remaining_in=remaining;st.complete=true;return st;
}
template<bool Diagnose>
SB_NOINLINE Work push(const Graph&g,U s,consumer::Workspace&w,U bound,
                     bool use_bound,L max_rows=std::numeric_limits<L>::max()){
    require(s<g.n()&&bound>0&&bound<=g.n(),"invalid push source/bound");
    auto&d=w.base.distance;auto&q=w.base.queue;std::fill(d.begin(),d.end(),-1);d[s]=0;q[0]=s;
    U head=0,tail=1;Work st;st.limit=bound;
    while(head<tail && (!use_bound||tail<bound)){
        if(head>=max_rows){st.seen=tail;return st;}
        U u=q[head++];for(L e=g.row()[u];e<g.row()[u+1];++e){if constexpr(Diagnose)++st.edges;
            U v=g.col()[e];if(d[v]<0){d[v]=d[u]+1;q[tail++]=v;}}
    }
    require(tail<=bound,"invalid push upper bound");st.seen=tail;st.complete=true;
    st.reason=(head<tail&&tail==bound)?(bound==g.n()?1:3):0;return st;
}
// Cache representation choices. Any cache is attached to immutable graph object.
// Direction's frontier queue is NOT the list of all discovered vertices.
// Hence TABLE publication explicitly scans complete distance[n], with cost counted.
enum class Cache {NONE,LAST,TABLE};
struct Mode {const char*name;bool is_push;unsigned flags;Cache cache;};
inline const std::vector<Mode>& modes(){static const std::vector<Mode>v={
 {"PUSH_MATCHED",true,0,Cache::NONE},
 {"PUSH_N",true,N,Cache::NONE},
 {"PUSH_RCC_TABLE",true,N|RCC,Cache::TABLE},
 {"DO_MATCHED",false,0,Cache::NONE},
 {"DO_N",false,N,Cache::NONE},
 {"DO_RIE",false,N|RIE,Cache::NONE},
 {"DO_RCC_LAST",false,N|RCC,Cache::LAST},
 {"DO_RIE_RCC_LAST",false,N|RIE|RCC,Cache::LAST},
 {"DO_RCC_TABLE",false,N|RCC,Cache::TABLE},
 {"DO_RIE_RCC_TABLE",false,N|RIE|RCC,Cache::TABLE},
 {"DO_TABLE_OFF",false,N,Cache::TABLE},
 {"DO_RIE_TABLE_OFF",false,N|RIE,Cache::TABLE}};return v;}
class Executor {
    std::shared_ptr<const Graph>g_;
    std::shared_ptr<const Reverse>r_;
    Mode mode_;
    std::vector<int>last_;
    std::vector<U>table_;
    U last_count_=0;
    bool retained_output_=false;
public:
    Executor(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,Mode mode):g_(std::move(g)),r_(std::move(r)),mode_(mode){
        require(bool(g_)&&g_->n()>0,"empty graph rejected");
        if(!mode_.is_push)require(r_&&r_->graph_ptr().get()==g_.get(),"builder reader identity");
        if(mode_.cache==Cache::LAST)last_.assign(g_->n(),-1);
        if(mode_.cache==Cache::TABLE)table_.assign(g_->n(),g_->n());
    }
    U bound(U s)const{require(s<g_->n(),"bound source");
        if(mode_.cache==Cache::LAST&&last_count_&&last_[s]>=0)return last_count_;
        if(mode_.cache==Cache::TABLE)return table_[s];
        return g_->n();}
    L cache_bytes()const{return 4*(L(last_.capacity())+table_.capacity());}
    void reset(){last_count_=0;retained_output_=false;
        std::fill(last_.begin(),last_.end(),-1);std::fill(table_.begin(),table_.end(),g_->n());}
    const std::vector<int>& output(const consumer::Workspace&w)const{return retained_output_?last_:w.base.distance;}
    const std::vector<U>&bounds()const{return table_;}
    template<bool Diagnose=false>Work run(U s,consumer::Workspace&w,L budget=std::numeric_limits<L>::max()){
        const U before=bound(s);const U used=(mode_.flags&RCC)?before:g_->n();
        retained_output_=false;
        Work st=mode_.is_push?push<Diagnose>(*g_,s,w,used,bool(mode_.flags),budget):
                    direction<Diagnose>(*g_,*r_,s,w,mode_.flags,used,budget);
        if(!st.complete)return st; // Abort does not replace/publish certificate.
        if(mode_.cache==Cache::LAST){last_.swap(w.base.distance);last_count_=st.seen;retained_output_=true;}
        else if(mode_.cache==Cache::TABLE && st.seen<before){
            for(U v=0;v<g_->n();++v){if constexpr(Diagnose)++st.publish_visits;
                if(w.base.distance[v]>=0&&table_[v]>st.seen){table_[v]=st.seen;if constexpr(Diagnose)++st.publish_writes;}}}
        return st;
    }
};
} // namespace stop_bridge
