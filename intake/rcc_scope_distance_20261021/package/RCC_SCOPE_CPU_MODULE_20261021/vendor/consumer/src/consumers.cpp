#include "consumers.hpp"
namespace consumer {
static void compatible(const Graph&g,const Reverse*r){require(r&&r->graph_ptr().get()==&g,"reverse graph/version mismatch");}
static void p0(const Graph&g,const Reverse*,U s,Workspace&w){independent::plan_a(g,s,w.base);}
static void p1(const Graph&g,const Reverse*r,U s,Workspace&w){compatible(g,r);independent::followup(*r,s,w.base);}

template<bool Trace,bool ForcePush>static void direction(const Graph&g,const Reverse&r,U s,Workspace&w,Diagnostic*d){
    require(s<g.n(),"BFS source");require(w.next.size()==g.n()&&w.bitmap.size()==(L(g.n())+63)/64,"policy workspace shape");
    std::fill(w.base.distance.begin(),w.base.distance.end(),-1);w.base.distance[s]=0;
    auto*front=&w.base.queue;auto*next=&w.next;(*front)[0]=s;
    L frontier=1,frontier_edges=g.row()[s+1]-g.row()[s],remaining=g.m()-(r.row()[s+1]-r.row()[s]);
    bool shadow_pull=false;U level=0;
    while(frontier){
        if(shadow_pull){if(frontier<std::max<L>(1,g.n()/BETA))shadow_pull=false;}
        else if(frontier_edges>remaining/ALPHA)shadow_pull=true;
        const bool pull=shadow_pull&&!ForcePush;
        Level trace;if constexpr(Trace){trace.level=level;trace.frontier=frontier;trace.frontier_edges=frontier_edges;trace.remaining_in=remaining;trace.shadow_pull=shadow_pull;trace.actual_pull=pull;}
        // P3 performs exactly the same shadow-policy bitmap construction as P2.
        if(shadow_pull){std::fill(w.bitmap.begin(),w.bitmap.end(),0);for(L i=0;i<frontier;++i){U u=(*front)[i];w.bitmap[u/64]|=L(1)<<(u%64);}if constexpr(Trace){trace.bitmap_words_cleared=w.bitmap.size();trace.bitmap_set_ops=frontier;trace.queue_reads+=frontier;}}
        L found=0,next_edges=0;
        auto discover=[&](U v){w.base.distance[v]=int(level)+1;(*next)[found++]=v;next_edges+=g.row()[v+1]-g.row()[v];L indegree=r.row()[v+1]-r.row()[v];require(indegree<=remaining,"remaining indegree underflow");remaining-=indegree;if constexpr(Trace){++trace.queue_writes;++trace.policy_vertex_updates;trace.policy_offset_reads+=4;}};
        if(pull){
            for(U v=0;v<g.n();++v){if constexpr(Trace)++trace.unvisited_vertex_tests;if(w.base.distance[v]>=0)continue;
                for(L p=r.row()[v];p<r.row()[v+1];++p){U u=r.source()[p];if constexpr(Trace){++trace.reverse_edges;++trace.bitmap_membership_tests;}if((w.bitmap[u/64]>>(u%64))&1){discover(v);break;}}
            }
        }else{
            for(L i=0;i<frontier;++i){U u=(*front)[i];if constexpr(Trace)++trace.queue_reads;
                for(L e=g.row()[u];e<g.row()[u+1];++e){U v=g.col()[e];if constexpr(Trace){++trace.csr_edges;++trace.neighbor_distance_tests;}if(w.base.distance[v]<0)discover(v);}
            }
        }
        if constexpr(Trace){trace.discovered=found;if(!level){++trace.queue_writes;++trace.policy_vertex_updates;trace.policy_offset_reads+=4;}d->levels.push_back(trace);}
        frontier=found;frontier_edges=next_edges;std::swap(front,next);++level;require(level<=L(g.n())+1,"BFS termination");
    }
    if constexpr(Trace)d->initialized_distance_vertices=g.n();
}
static void p2(const Graph&g,const Reverse*r,U s,Workspace&w){compatible(g,r);direction<false,false>(g,*r,s,w,nullptr);}
static void p3(const Graph&g,const Reverse*r,U s,Workspace&w){compatible(g,r);direction<false,true>(g,*r,s,w,nullptr);}
Fn function(Mode mode){switch(mode){case Mode::QUEUE_PUSH:return p0;case Mode::PURE_PULL:return p1;case Mode::DIRECTION:return p2;case Mode::STATS_PUSH:return p3;}throw std::runtime_error("invalid consumer mode");}

Diagnostic diagnose(Mode mode,const Graph&g,const Reverse&r,U s,Workspace&w){
    compatible(g,&r);require(U(mode)<4,"invalid diagnostic mode");require(s<g.n(),"BFS source");Diagnostic d;
    if(mode==Mode::DIRECTION){direction<true,false>(g,r,s,w,&d);return d;}
    if(mode==Mode::STATS_PUSH){direction<true,true>(g,r,s,w,&d);return d;}
    std::fill(w.base.distance.begin(),w.base.distance.end(),-1);w.base.distance[s]=0;d.initialized_distance_vertices=g.n();
    if(mode==Mode::QUEUE_PUSH){
        L head=0,tail=1;w.base.queue[0]=s;U level=0;
        while(head<tail){L end=tail;Level trace;trace.level=level;trace.frontier=end-head;if(!level)trace.queue_writes=1;
            while(head<end){U u=w.base.queue[head++];++trace.queue_reads;for(L e=g.row()[u];e<g.row()[u+1];++e){++trace.csr_edges;++trace.neighbor_distance_tests;U v=g.col()[e];if(w.base.distance[v]<0){w.base.distance[v]=w.base.distance[u]+1;w.base.queue[tail++]=v;++trace.queue_writes;++trace.discovered;}}}
            trace.frontier_edges=trace.csr_edges;d.levels.push_back(trace);++level;
        }
    }else{
        U level=0;bool changed=true;L frontier=1;
        while(changed){changed=false;Level trace;trace.level=level;trace.frontier=frontier;trace.actual_pull=trace.shadow_pull=true;
            for(U v=0;v<g.n();++v){++trace.unvisited_vertex_tests;if(w.base.distance[v]<0)for(L p=r.row()[v];p<r.row()[v+1];++p){++trace.reverse_edges;++trace.neighbor_distance_tests;if(w.base.distance[r.source()[p]]==int(level)){w.base.distance[v]=int(level)+1;changed=true;++trace.discovered;break;}}}
            frontier=trace.discovered;d.levels.push_back(trace);++level;require(level<=L(g.n())+1,"BFS termination");
        }
    }return d;
}
} // namespace consumer
