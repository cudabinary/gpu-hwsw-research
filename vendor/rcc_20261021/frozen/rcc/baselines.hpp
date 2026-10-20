#pragma once
#include "rcc.hpp"
namespace rcc {
struct Reverse {
    std::vector<Offset> row;
    std::vector<Vertex> src;
    explicit Reverse(const Graph& g):row(std::size_t(g.n())+1,0),src(g.m()){
        for(auto v:g.col())++row[v+1];
        for(Vertex v=0;v<g.n();++v)row[v+1]+=row[v];
        auto cur=row;
        for(Vertex u=0;u<g.n();++u)for(Offset e=g.row()[u];e<g.row()[u+1];++e)src[cur[g.col()[e]]++]=u;
    }
    std::size_t bytes()const{return row.capacity()*8+src.capacity()*4;}
};
struct DirectionWorkspace {
    std::vector<Vertex> next;
    explicit DirectionWorkspace(Vertex n):next(n){}
};
// Conventional full reverse pull baseline (preserved failure path).
template<bool Diagnose=false>
Run pure_pull(const Graph& g,const Reverse& r,Vertex s,Workspace& w){
    if(s>=g.n())throw std::invalid_argument("source");
    std::fill(w.distance.begin(),w.distance.end(),-1);w.distance[s]=0;
    Run st;Vertex discovered=1;std::int32_t level=0;bool changed=true;
    while(changed){changed=false;
        for(Vertex v=0;v<g.n();++v)if(w.distance[v]<0){
            for(Offset p=r.row[v];p<r.row[v+1];++p){if constexpr(Diagnose)++st.edges_read;
                if(w.distance[r.src[p]]==level){w.distance[v]=level+1;++discovered;changed=true;break;}}
        }
        ++level;
    }
    st.complete=true;st.discovered=discovered;st.bound=g.n();return st;
}
// Existing direction-optimizing principle, fixed alpha=15,beta=24, no tuning.
// Policy statistics + queue rebuilding costs are included. Not a new method.
template<bool Diagnose=false>
Run direction(const Graph&g,const Reverse&r,Vertex s,Workspace&w,DirectionWorkspace&dw,Vertex upper=0){
    if(s>=g.n())throw std::invalid_argument("source");
    if(!upper) upper=g.n();
    if(upper>g.n())throw std::invalid_argument("direction bound");
    auto&d=w.distance;std::fill(d.begin(),d.end(),-1);d[s]=0;
    auto*front=w.queue.data();auto*next=dw.next.data();Vertex nf=1,seen=1;front[0]=s;
    Offset scout=g.row()[s+1]-g.row()[s],remaining=g.m();bool pull=false;std::int32_t depth=0;Run st;
    while(nf && seen<upper){
        if(!pull && scout>remaining/15)pull=true;
        else if(pull && nf<std::max<Vertex>(1,g.n()/24))pull=false;
        Vertex nn=0;Offset next_sc=0;
        if(pull){
            for(Vertex v=0;v<g.n();++v)if(d[v]<0){
                for(Offset p=r.row[v];p<r.row[v+1];++p){if constexpr(Diagnose)++st.edges_read;
                    if(d[r.src[p]]==depth){d[v]=depth+1;next[nn++]=v;next_sc+=g.row()[v+1]-g.row()[v];break;}}
            }
        }else{
            for(Vertex j=0;j<nf;++j){Vertex u=front[j];
                for(Offset e=g.row()[u];e<g.row()[u+1];++e){if constexpr(Diagnose)++st.edges_read;Vertex v=g.col()[e];
                    if(d[v]<0){d[v]=depth+1;next[nn++]=v;next_sc+=g.row()[v+1]-g.row()[v];}}
            }
        }
        remaining=scout>remaining?0:remaining-scout;scout=next_sc;
        seen+=nn;nf=nn;std::swap(front,next);++depth;
    }
    if(seen>upper)throw std::logic_error("direction exceeded bound");
    st.complete=true;st.discovered=seen;st.bound=upper;st.stopped_by_bound=(seen==upper && nf>0);return st;
}
// Dense outgoing-row bitmap. Includes full construction in cold batch timing.
class FullBitmap {
    std::size_t words_;
    std::vector<std::uint64_t> bits_,visited_,next_;
public:
    explicit FullBitmap(const Graph&g):words_((std::size_t(g.n())+63)/64),bits_(std::size_t(g.n())*words_,0),visited_(words_),next_(words_){
        for(Vertex u=0;u<g.n();++u)for(Offset e=g.row()[u];e<g.row()[u+1];++e){Vertex v=g.col()[e];bits_[std::size_t(u)*words_+v/64]|=std::uint64_t(1)<<(v%64);}
    }
    std::size_t bytes()const{return (bits_.capacity()+visited_.capacity()+next_.capacity())*8;}
    Run run(const Graph&g,Vertex s,Workspace&w){
        if(s>=g.n())throw std::invalid_argument("source");
        auto&d=w.distance;std::fill(d.begin(),d.end(),-1);std::fill(visited_.begin(),visited_.end(),0);
        d[s]=0;visited_[s/64]|=std::uint64_t(1)<<(s%64);w.queue[0]=s;Vertex head=0,end=1;std::int32_t depth=0;
        while(head<end && end<g.n()){
            std::fill(next_.begin(),next_.end(),0);Vertex old=end;
            for(Vertex j=head;j<old;++j){std::size_t p=std::size_t(w.queue[j])*words_;for(std::size_t k=0;k<words_;++k)next_[k]|=bits_[p+k];}
            for(std::size_t k=0;k<words_;++k){auto z=next_[k]&~visited_[k];visited_[k]|=z;
                while(z){Vertex v=Vertex(k*64+unsigned(__builtin_ctzll(z)));d[v]=depth+1;w.queue[end++]=v;z&=z-1;}}
            head=old;++depth;
        }
        Run r;r.complete=true;r.discovered=end;r.bound=g.n();return r;
    }
};

// RCC wrapper around the conventional direction consumer. The previous output
// is retained by vector swap: no per-edge or per-vertex certificate construction.
class DirectionClosure {
    GraphPtr g_;
    std::vector<std::int32_t> previous_;
    Vertex previous_count_=0;
public:
    explicit DirectionClosure(GraphPtr g):g_(checked_graph(std::move(g))),previous_(g_->n(),-1){}
    template<bool Diagnose=false> Run first(Vertex s, Workspace&w){
        Run st=queue_bfs<Diagnose>(*g_,s,w,g_->n());
        previous_.swap(w.distance);previous_count_=st.discovered;return st;
    }
    template<bool Diagnose=false> Run run(const Reverse&r,Vertex s,Workspace&w,DirectionWorkspace&dw){
        if(s>=g_->n())throw std::out_of_range("source");
        Vertex upper=previous_count_ && previous_[s]>=0?previous_count_:g_->n();
        Run st=direction<Diagnose>(*g_,r,s,w,dw,upper);
        previous_.swap(w.distance);previous_count_=st.discovered;return st;
    }
    const std::vector<std::int32_t>&distance()const{return previous_;}
    void release_result(Workspace&w){previous_.swap(w.distance);previous_count_=0;}
};

// A strong conventional certificate baseline: weak connected component sizes.
// DSU preprocessing scans ALL edges; valid upper bounds also for directed BFS.
class WeakComponents {
    std::vector<Vertex>parent_,size_,bound_;
    Vertex root(Vertex u){while(parent_[u]!=u){parent_[u]=parent_[parent_[u]];u=parent_[u];}return u;}
public:
    explicit WeakComponents(const Graph&g):parent_(g.n()),size_(g.n(),1),bound_(g.n()){
        for(Vertex u=0;u<g.n();++u)parent_[u]=u;
        for(Vertex u=0;u<g.n();++u)for(Offset e=g.row()[u];e<g.row()[u+1];++e){
            auto a=root(u),b=root(g.col()[e]);if(a!=b){if(size_[a]<size_[b])std::swap(a,b);parent_[b]=a;size_[a]+=size_[b];}}
        for(Vertex v=0;v<g.n();++v)bound_[v]=size_[root(v)];
    }
    Vertex bound(Vertex s)const{return bound_.at(s);}
    std::size_t bytes()const{return (parent_.capacity()+size_.capacity()+bound_.capacity())*4;}
};

} //namespace
