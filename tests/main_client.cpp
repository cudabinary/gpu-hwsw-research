// This MAIN executable knows only the versioned public API, never RCC internals.
#include "rcc/v1.hpp"
#include <dlfcn.h>
#include <deque>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <atomic>
#include <fstream>
#include <sstream>
using namespace rcc_api;
static unsigned checks=0,arrays=0;
static void check(bool b,const char*m){++checks;if(!b)throw std::runtime_error(m);}
static std::vector<int> oracle(const Graph&g,U s){
 std::vector<int>d(g.n,-1);std::deque<U>q{s};d[s]=0;
 while(!q.empty()){auto u=q.front();q.pop_front();for(L p=g.row[u];p<g.row[u+1];++p)if(d[g.col[p]]<0){d[g.col[p]]=d[u]+1;q.push_back(g.col[p]);}}
 return d;
}
int main(int argc,char**argv){try{
 check(argc==2,"plugin path");void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h)throw std::runtime_error(dlerror());
 // Modules stay mapped until process exit; never unload code while readers own results.
 auto create=reinterpret_cast<Create>(dlsym(h,"rcc_create"));auto destroy=reinterpret_cast<Destroy>(dlsym(h,"rcc_destroy"));
 check(create&&destroy,"exports");check(create(API_VERSION+1)==nullptr,"ABI rejection");
 auto*m=create(API_VERSION);check(m,"factory");auto cap=m->capabilities();check(cap.api_version==API_VERSION&&cap.cpu&&!cap.cuda,"capabilities");
 auto g=Graph::from_edges("lifecycle",1,6,{{0,1},{0,1},{1,2},{2,0},{4,5},{5,5}});
 auto compare=[&](const Reply&r,const GraphPtr&graph,U s){check(r.status==Status::OK&&bool(r.output),"completed result");check(r.output->graph()==graph&&r.output->source()==s,"result identity");check(r.output->distance()==oracle(*graph,s),"full array");++arrays;};
 check(m->run({g,0}).status==Status::NOT_PREPARED,"unprepared");
 Options gpu;gpu.backend=Backend::CUDA;check(m->prepare(g,gpu).status==Status::UNSUPPORTED_BACKEND,"GPU fail closed");
 check(m->prepare(g,{}).status==Status::OK,"prepare");check(!m->can_apply(g,1),"no certificate");
 auto first=m->run({g,0});compare(first,g,0);auto held=first.output;
 bool rcc=std::string(cap.implementation)!="baseline-1";
 check(m->can_apply(g,1)==rcc,"completed seed certificate");
 auto next=m->run({g,1});compare(next,g,1);check(next.metrics.certificate_applied==rcc,"certificate use");
 Request disabled{g,2};disabled.enabled=false;auto dis=m->run(disabled);compare(dis,g,2);check(dis.metrics.fallback,"disabled fallback");
 auto same=Graph::from_edges("lifecycle",1,6,{{0,1},{1,2}});
 auto other=Graph::from_edges("different",1,6,{{0,1}});
 auto changed=Graph::from_edges("lifecycle",2,6,{{0,4},{4,5}});
 for(auto bad:{same,other,changed}){check(!m->can_apply(bad,1),"wrong graph certificate");check(m->run({bad,0}).status==Status::INVALID_GRAPH,"wrong graph run");}
 Request cancel{g,0};cancel.cancelled=true;check(m->run(cancel).status==Status::CANCELLED,"pre-cancel");
 auto before=m->can_apply(g,1);Request fail{g,4};fail.fail_output_allocation=true;
 auto failed=m->run(fail);check(failed.status==Status::ALLOCATION_FAILED&&!failed.output,"output allocation failure");check(m->can_apply(g,1)==before,"failed publication atomicity");
 m->invalidate();check(!m->can_apply(g,1),"invalidate");Request budget{g,0};budget.row_budget=0;
 auto partial=m->run(budget);check(partial.status==Status::CANCELLED&&!partial.output,"row budget cancellation");check(!m->can_apply(g,1),"no partial certificate");
 compare(m->update({g,0}),g,0);check(m->can_apply(g,1)==rcc,"update generation");
 check(m->run({g,6}).status==Status::INVALID_SOURCE,"invalid source");
 std::atomic<bool> reader_ok=true;
 std::thread reader([&]{for(int i=0;i<1000;++i)if(held->distance()!=std::vector<int>({0,1,2,-1,-1,-1}))reader_ok=false;});
 for(int i=0;i<40;++i){m->release();check(m->prepare(changed,{}).status==Status::OK,"rebind");compare(m->run({changed,0}),changed,0);m->invalidate();}
 reader.join();check(reader_ok,"reader survives release/rebind");
 Options low;low.cache_limit=0;check(m->prepare(g,low).status==Status::OK,"cache budget fallback");compare(m->run({g,0}),g,0);check(!m->can_apply(g,1),"no certificate with failed cache");
 Options inj;inj.fail_cache_allocation=true;check(m->prepare(g,inj).status==Status::OK,"injected cache failure fallback");compare(m->run({g,1}),g,1);
 Options off;off.enabled=false;compare(m->prepare(g,off,0),g,0);check(!m->can_apply(g,1),"disabled prepare seed");
 for(U mask=0;mask<512;++mask){
  std::vector<std::pair<U,U>>edges;for(U i=0;i<9;++i)if(mask&(1u<<i))edges.emplace_back(i/3,i%3);
  if(mask%7==0&&!edges.empty())edges.push_back(edges.front());
  auto small=Graph::from_edges("exhaustive",mask+1,3,edges);check(m->prepare(small,{}).status==Status::OK,"exhaustive prepare");
  for(U s:{0u,1u,2u,0u})compare(m->run({small,s}),small,s);
 }
 for(auto [file,n]:std::vector<std::pair<std::string,U>>{{"livejournal_sampled_4096.edges",4096},{"google_sampled_1024.edges",1024},{"road_sampled_64.edges",64},{"scc4_d32.edges",4096}}){
  std::ifstream f("vendor/rcc_20261021/fixtures/"+file);check(bool(f),"fixture open");std::string line;std::vector<std::pair<U,U>>edges;
  while(std::getline(f,line)){if(line.empty()||line[0]=='#'||line[0]=='%')continue;std::istringstream in(line);U u,v;check(bool(in>>u>>v),"fixture edge");edges.emplace_back(u,v);}
  auto fixture=Graph::from_edges(file,1,n,edges);check(m->prepare(fixture,{}).status==Status::OK,"fixture prepare");
  for(U s:{0u,17u,34u,0u})compare(m->run({fixture,s}),fixture,s);
 }
 m->release();check(held->distance()==oracle(*g,0),"owned reader final");check(m->run({g,0}).status==Status::NOT_PREPARED,"released");
 std::string implementation=cap.implementation;destroy(m);
 std::cout<<"{\"status\":\"PASS\",\"implementation\":\""<<implementation<<"\",\"api\":65536,\"checks\":"<<checks<<",\"arrays\":"<<arrays<<",\"graphs_exhaustive\":512,\"cuda_runtime\":\"UNSUPPORTED_NOT_TESTED\"}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
