#pragma once
// Stage 2: previous exact distance result -> per-level admissibility bound.
// No claim of new triangle inequality / landmark algorithm.
#include "closure_scope.hpp"
namespace rcc_scope {
enum class Guard {COUNT_ONLY,CLOSURE_ONLY,DISTANCE_RADIUS,FRONTIER_MAX};
struct DistanceWork: Work { L outside_skips=0,future_level_skips=0,previous_distance_reads=0; };
class DistanceExecutor {
    std::shared_ptr<const Graph>g_;std::shared_ptr<const Reverse>r_;Guard guard_;
    std::vector<int>previous_;U reached_=0;bool use_prev_=false,retained_=false;
public:
    DistanceExecutor(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,Guard guard,L budget=std::numeric_limits<L>::max()):g_(std::move(g)),r_(std::move(r)),guard_(guard){
        require(g_&&r_&&g_.get()==r_->graph_ptr().get()&&g_->n()>0,"distance guard binding");
        if(4*L(g_->n())<=budget)try{previous_.assign(g_->n(),-1);}catch(const std::bad_alloc&){previous_.clear();}
    }
    L bytes()const{return 4*L(previous_.capacity());}
    void reset(){reached_=0;use_prev_=retained_=false;std::fill(previous_.begin(),previous_.end(),-1);}
    const std::vector<int>&output(const consumer::Workspace&w)const{return retained_?previous_:w.base.distance;}
    U bound(U s)const{require(s<g_->n(),"source range");return use_prev_&&previous_[s]>=0?reached_:g_->n();}
    template<bool D=false>SB_NOINLINE DistanceWork run(U s,consumer::Workspace&w,L max_levels=std::numeric_limits<L>::max()){
        const Graph&g=*g_;const Reverse&r=*r_;
        require(s<g.n()&&w.base.distance.size()==g.n()&&w.next.size()==g.n(),"guard workspace/source");
        const bool hit=use_prev_&&previous_[s]>=0;const U upper=hit?reached_:g.n();
        const L old_s=hit?L(previous_[s]):0;
        retained_=false;auto&d=w.base.distance;std::fill(d.begin(),d.end(),-1);d[s]=0;
        auto*front=&w.base.queue;auto*next=&w.next;(*front)[0]=s;
        L nf=1,fe=g.row()[s+1]-g.row()[s],remaining=g.m()-(r.row()[s+1]-r.row()[s]);
        U seen=1,depth=0;bool pull=false;DistanceWork st;st.hit=hit;st.domain_size=upper;
        while(nf){
            require(seen<=upper,"distance bound mismatch");
            if(seen==upper){st.stop_reason=upper==g.n()?1:3;break;}
            if(!remaining){st.stop_reason=2;break;}
            if(depth>=max_levels){st.seen=seen;return st;}
            if(pull){if(nf<std::max<L>(1,g.n()/consumer::BETA))pull=false;}
            else if(fe>remaining/consumer::ALPHA)pull=true;
            L horizon=old_s+L(depth)+1;
            if(pull){std::fill(w.bitmap.begin(),w.bitmap.end(),0);
                if(hit&&guard_==Guard::FRONTIER_MAX)horizon=0;
                for(L i=0;i<nf;++i){U u=(*front)[i];w.bitmap[u/64]|=L(1)<<(u%64);
                    if(hit&&guard_==Guard::FRONTIER_MAX){require(previous_[u]>=0,"frontier escapes closure");horizon=std::max(horizon,L(previous_[u])+1);if constexpr(D)++st.previous_distance_reads;}}
                if constexpr(D){st.bitmap_clear+=w.bitmap.size();st.bitmap_set+=nf;}}
            L found=0,next_edges=0;
            auto discover=[&](U v){d[v]=int(depth)+1;(*next)[found++]=v;next_edges+=g.row()[v+1]-g.row()[v];L k=r.row()[v+1]-r.row()[v];require(k<=remaining,"remaining underflow");remaining-=k;++seen;};
            if(pull){for(U v=0;v<g.n();++v){if constexpr(D)++st.vertex_tests;if(d[v]>=0)continue;
                if(hit&&guard_!=Guard::COUNT_ONLY){int ov=previous_[v];if constexpr(D)++st.previous_distance_reads;
                    if(ov<0){if constexpr(D)++st.outside_skips;continue;}
                    if(guard_!=Guard::CLOSURE_ONLY&&L(ov)>horizon){if constexpr(D)++st.future_level_skips;continue;}}
                for(L e=r.row()[v];e<r.row()[v+1];++e){if constexpr(D)++st.edges;U u=r.source()[e];if((w.bitmap[u/64]>>(u%64))&1u){discover(v);break;}}}}
            else{for(L i=0;i<nf;++i){U u=(*front)[i];for(L e=g.row()[u];e<g.row()[u+1];++e){if constexpr(D){++st.edges;}U v=g.col()[e];if(d[v]<0)discover(v);}}}
            nf=found;fe=next_edges;std::swap(front,next);++depth;if constexpr(D)++st.levels;
        }
        st.complete=true;st.seen=seen;st.remaining_global=remaining;
        if(!previous_.empty()){previous_.swap(w.base.distance);reached_=seen;use_prev_=retained_=true;st.published=true;}
        st.cache_live_bytes=bytes();st.cache_peak_bytes=bytes();return st;
    }
};
} // namespace rcc_scope
