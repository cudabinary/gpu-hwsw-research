#pragma once
// Faithful experimental port of the received distance_guard.hpp loop. The
// certificate is a completed API-owned immutable Output, not an imported array.
#include "stop_bridge.hpp"
namespace dg_kernel {
using namespace independent;
struct Work:stop_bridge::Work {L old_reads=0,future_skips=0,outside_skips=0;};
inline Work run(const Graph&g,const Reverse&r,U s,consumer::Workspace&w,
                const std::vector<int>&previous,U upper,unsigned guard){
 require(r.graph_ptr().get()==&g&&s<g.n()&&previous.size()==g.n()&&previous[s]>=0,"guard binding");
 auto&d=w.base.distance;std::fill(d.begin(),d.end(),-1);d[s]=0;
 auto*front=&w.base.queue;auto*next=&w.next;(*front)[0]=s;
 L nf=1,fe=g.row()[s+1]-g.row()[s],remaining=g.m()-(r.row()[s+1]-r.row()[s]);
 U seen=1,depth=0;bool pull=false;Work st;st.limit=upper;
 while(nf){
  require(seen<=upper,"invalid completed upper bound");
  if(seen==upper){st.reason=upper==g.n()?1:3;break;}
  if(!remaining){st.reason=2;break;}
  if(pull){if(nf<std::max<L>(1,g.n()/consumer::BETA))pull=false;}
  else if(fe>remaining/consumer::ALPHA)pull=true;
  L horizon=L(previous[s])+depth+1;
  if(pull){
   std::fill(w.bitmap.begin(),w.bitmap.end(),0);
   if(guard==3)horizon=0;
   for(L i=0;i<nf;++i){U u=(*front)[i];w.bitmap[u/64]|=L(1)<<(u%64);
    if(guard==3){require(previous[u]>=0,"frontier outside certified closure");horizon=std::max(horizon,L(previous[u])+1);++st.old_reads;}
   }
   st.bitmap_clear+=w.bitmap.size();st.bitmap_set+=nf;
  }
  L found=0,next_edges=0;
  auto discover=[&](U v){d[v]=int(depth)+1;(*next)[found++]=v;next_edges+=g.row()[v+1]-g.row()[v];L k=r.row()[v+1]-r.row()[v];require(k<=remaining,"remaining underflow");remaining-=k;++seen;};
  if(pull){
   for(U v=0;v<g.n();++v){++st.vertex_tests;if(d[v]>=0)continue;
    if(guard!=0){int old=previous[v];++st.old_reads;if(old<0){++st.outside_skips;continue;}
     if(guard!=1&&L(old)>horizon){++st.future_skips;continue;}}
    for(L e=r.row()[v];e<r.row()[v+1];++e){++st.edges;U u=r.source()[e];if((w.bitmap[u/64]>>(u%64))&1u){discover(v);break;}}
   }
  }else for(L i=0;i<nf;++i){U u=(*front)[i];for(L e=g.row()[u];e<g.row()[u+1];++e){++st.edges;U v=g.col()[e];if(d[v]<0)discover(v);}}
  nf=found;fe=next_edges;std::swap(front,next);++depth;++st.levels;
 }
 st.complete=true;st.seen=seen;st.remaining_in=remaining;return st;
}
}
