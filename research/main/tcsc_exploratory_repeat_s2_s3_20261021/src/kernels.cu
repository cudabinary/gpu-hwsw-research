#include "abi.hpp"
using namespace rgpu;
__device__ void bad(View d,U code){atomicCAS(d.error,0u,code);}
extern "C" __global__ void r_init(View d,U source){
 U v=blockIdx.x*blockDim.x+threadIdx.x;
 if(v<d.n)d.distance[v]=v==source?0:-1;
 if(!v){d.front[0]=source;*d.error=0;}
}
extern "C" __global__ void r_mark(View d,U count){
 U i=blockIdx.x*blockDim.x+threadIdx.x;
 if(i<count){U u=d.front[i];if(u>=d.n){bad(d,1);return;}atomicOr(d.bitmap+u/64,1ull<<(u%64));}
}
__device__ void append(View d,U v,bool stats){
 L at=atomicAdd(&d.counter->found,1ull);
 if(at>=d.n){bad(d,2);return;}d.next[at]=v;
 if(stats){atomicAdd(&d.counter->out_edges,d.row[v+1]-d.row[v]);atomicAdd(&d.counter->in_edges,d.rrow[v+1]-d.rrow[v]);}
}
extern "C" __global__ void r_push(View d,U count,U level,U stats){
 U i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=count)return;U u=d.front[i];
 if(u>=d.n){bad(d,3);return;}
 L begin=d.row[u],end=d.row[u+1];if(begin>end||end>d.m){bad(d,4);return;}
 for(L e=begin;e<end;++e){U v=d.col[e];if(v>=d.n){bad(d,5);return;}
  if(atomicCAS(d.distance+v,-1,int(level)+1)==-1)append(d,v,stats);}
}
extern "C" __global__ void r_pull(View d,U level){
 U v=blockIdx.x*blockDim.x+threadIdx.x;if(v>=d.n||atomicAdd(d.distance+v,0)>=0)return;
 L begin=d.rrow[v],end=d.rrow[v+1];if(begin>end||end>d.m){bad(d,6);return;}
 for(L e=begin;e<end;++e){U u=d.rsource[e];if(u>=d.n){bad(d,7);return;}
  if((d.bitmap[u/64]>>(u%64))&1){if(atomicCAS(d.distance+v,-1,int(level)+1)==-1)append(d,v,true);break;}}
}
