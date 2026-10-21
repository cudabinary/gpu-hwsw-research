#pragma once
#include <cstdint>
#include <stdexcept>

// Host-only controls. No CUDA ABI, kernel, reverse-builder or RCC API change.
namespace host_control {
using U=std::uint32_t;using L=std::uint64_t;
inline bool supported(U mode){return mode==0||mode==4||mode==5||mode==6||mode==7||mode==8;}
inline bool static_bound_mode(U mode){return mode==7||mode==8;}
inline bool degree_stats(U mode){return mode>=2&&mode!=7;}
inline bool direction(U mode){return mode>=2&&mode!=6&&mode!=7&&mode!=8;}
inline bool frontier_zero(U mode){return mode==4||mode==5||mode==8;}
inline bool dynamic_rie(U mode){return mode==3||mode==5;}
inline U stop(U mode,U seen,U n,L frontier_edges,L remaining,U bound){
    if(seen==n)return 1;
    if(frontier_zero(mode)&&frontier_edges==0)return 4;
    if(static_bound_mode(mode)&&seen==bound)return 5;
    if(dynamic_rie(mode)&&remaining==0)return 2;
    return 0;
}

// Complete exact immutable reverse degrees are a prerequisite. Structural
// checks alone do not certify that a histogram belongs to the CSR's edges.
class IncomingBound {
    const void*graph_=nullptr;const void*reverse_=nullptr;
    U n_=0,positive_=0;L m_=0,version_=0;bool ready_=false;
public:
    template<class G,class R>static IncomingBound prepare(const G&g,const R&r){
        if(!g.n()||!g.version()||r.graph_ptr().get()!=&g||r.graph().version()!=g.version())
            throw std::invalid_argument("static bound graph/reverse identity");
        const auto*row=r.row();
        if(!row||row[0]!=0||row[g.n()]!=g.m())throw std::invalid_argument("static bound row shape");
        IncomingBound result;
        for(U v=0;v<g.n();++v){
            if(row[v]>row[v+1])throw std::invalid_argument("static bound row order");
            result.positive_+=row[v]!=row[v+1];
        }
        result.graph_=&g;result.reverse_=&r;result.n_=g.n();result.m_=g.m();result.version_=g.version();
        result.ready_=true;return result;
    }
    template<class G,class R>bool can_apply(const G&g,const R&r)const{
        return ready_&&graph_==&g&&reverse_==&r&&n_==g.n()&&m_==g.m()&&version_==g.version()
            &&r.graph_ptr().get()==&g&&r.graph().version()==version_;
    }
    template<class G,class R>U limit(const G&g,const R&r,U source)const{
        if(source>=g.n())throw std::invalid_argument("static bound source");
        if(!can_apply(g,r))return g.n(); // Exact EARLY_N fallback for this certificate.
        return positive_+U(r.row()[source]==r.row()[source+1]);
    }
    U positive_vertices()const{return positive_;}
};
}
