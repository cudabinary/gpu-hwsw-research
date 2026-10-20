// Independent API caller. The frozen MAIN client is run separately, unchanged.
#include "rcc/v1.hpp"
#include "dg_api_audit.hpp"
#include <algorithm>
#include <chrono>
#include <deque>
#include <dlfcn.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <sys/resource.h>
using namespace rcc_api;
using Clock=std::chrono::steady_clock;
static double ns(Clock::time_point t){return std::chrono::duration<double,std::nano>(Clock::now()-t).count();}
static void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
static const std::string package="intake/rcc_scope_distance_20261021/package/RCC_SCOPE_CPU_MODULE_20261021/fixtures/";
static const std::string build="build/dg_api_20261021/";
static const std::vector<std::string>names={"BFS_DEPLOYED","TABLE_DEPLOYED","LAST_DEPLOYED","PUSH_MATCHED","TABLE_MATCHED","LAST_MATCHED","OLD_P2","RIE","RIE_TABLE","DG_COUNT","DG_CLOSURE","DG_RADIUS","DG_FRONTIER","EXACT_REUSE"};
struct Library{Create create;Destroy destroy;dg_audit::Snapshot snapshot=nullptr;};
static Library load(const std::string&path){
 void*h=dlopen(path.c_str(),RTLD_NOW|RTLD_LOCAL);if(!h)throw std::runtime_error(dlerror());
 auto c=reinterpret_cast<Create>(dlsym(h,"rcc_create"));auto d=reinterpret_cast<Destroy>(dlsym(h,"rcc_destroy"));
 need(c&&d&&!c(0),"factory ABI");return {c,d,reinterpret_cast<dg_audit::Snapshot>(dlsym(h,"dg_audit_snapshot"))};
 // Libraries intentionally remain mapped while any owned output can exist.
}
static Library libraries[2][14];
static bool phase_run=false;
static double open_libraries(bool phases){auto start=Clock::now();
 phase_run=phases;
 for(unsigned p=0;p<2;++p)for(unsigned k=0;k<14;++k){
  std::string file=k==0?"build/baseline.so":k==1?"build/rcc_table.so":k==2?"build/rcc_last.so":build+"p"+std::to_string(k-3)+"_"+std::to_string(p)+(phases?"_phase.so":".so");
  libraries[p][k]=load(file);
 }return ns(start);
}
static std::vector<int> oracle(const Graph&g,U s){
 std::vector<int>d(g.n,-1);d[s]=0;std::deque<U>q{s};while(!q.empty()){auto u=q.front();q.pop_front();for(L e=g.row[u];e<g.row[u+1];++e){auto v=g.col[e];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;
}
struct Case{std::string name,file,schedule;U n;std::vector<U>sources;GraphPtr graph;std::vector<std::vector<int>>expected;};
static auto cases(bool timing){std::vector<Case>out;
 for(std::string schedule:{"legacy","unique"}){
  std::ifstream in(package+"scope_cases_"+schedule+".txt");need(bool(in),"case file");std::string line;
  while(std::getline(in,line)){Case c;c.schedule=schedule;std::istringstream row(line);row>>c.name>>c.file>>c.n;
   if(timing&&c.name!="google_sampled_1024"&&c.name!="livejournal_sampled_4096"&&c.name!="oneway_dense")continue;
   U s;while(row>>s)c.sources.push_back(s);need(c.sources.size()==33,"sources");
   std::ifstream edges(package+c.file);need(bool(edges),"graph file");std::vector<std::pair<U,U>>ev;
   while(std::getline(edges,line)){if(line.empty()||line[0]=='#'||line[0]=='%')continue;std::istringstream e(line);U u,v;need(bool(e>>u>>v),"edge");ev.emplace_back(u,v);}
   c.graph=Graph::from_edges(c.file,20261021,c.n,ev);for(auto source:c.sources)c.expected.push_back(oracle(*c.graph,source));out.push_back(std::move(c));
  }
 }need(out.size()==(timing?6:24),"case count");return out;
}
struct Timing{
 double service=0,prepare=0,queries=0,history=0,validation=0,release=0,lifecycle=0,module_release=0;
 double algorithm=0,allocation=0,copy=0,maintenance=0,lazy_reverse=0,internal_run=0,prep_graph=0,prep_reverse=0,prep_workspace=0;
 L arrays=0,edges=0,cache=0,csr=0,copies=0,old_reads=0,future_skips=0,outside_skips=0,certificates=0,fallbacks=0;
 bool edge_available=true;
};
static Timing service(const Case&c,unsigned k,bool ready,U q,std::ostream*dump=nullptr,std::ostream*work=nullptr){
 auto&lib=libraries[ready?0:1][k];Timing st;std::vector<Result>outputs;auto life=Clock::now();
 auto start=Clock::now();Module*m=lib.create(API_VERSION);need(m,"module allocation");
 auto prep=Clock::now();need(m->prepare(c.graph,{}).status==Status::OK,"prepare");st.prepare=ns(prep);
 if(lib.snapshot&&(phase_run||work)){dg_audit::Phases p;need(lib.snapshot(m,&p),"prepare phases");st.prep_graph=p.prepare_graph_ns;st.prep_reverse=p.prepare_reverse_ns;st.prep_workspace=p.prepare_workspace_ns;}
 if(ready){st.history=ns(start);start=Clock::now();}
 outputs.reserve(q+1);
 auto queries=Clock::now();
 for(U i=0;i<=q;++i){
  // Include an explicit public applicability call in every API service.
  bool applicable=m->can_apply(c.graph,c.sources[i]);(void)applicable;
  Reply r=m->run({c.graph,c.sources[i]});need(r.status==Status::OK&&bool(r.output),"run");
  st.edges+=r.metrics.inspected_edges;st.cache=std::max(st.cache,r.metrics.cache_bytes);st.csr=std::max(st.csr,r.metrics.adapter_csr_bytes);st.copies+=r.metrics.output_copy_elements;st.certificates+=r.metrics.certificate_applied;st.fallbacks+=r.metrics.fallback;
  dg_audit::Phases p;if(lib.snapshot&&(phase_run||work)){need(lib.snapshot(m,&p),"phase snapshot");st.edge_available&=p.exact_edge_counter;st.algorithm+=p.algorithm_ns;st.allocation+=p.allocation_ns;st.copy+=p.copy_ns;st.maintenance+=p.maintenance_ns;st.lazy_reverse+=p.lazy_reverse_ns;st.internal_run+=p.total_run_ns;st.old_reads+=p.old_reads;st.future_skips+=p.future_skips;st.outside_skips+=p.outside_skips;}
  if(k==6)st.edge_available=false;
  if(work)*work<<c.name<<','<<c.schedule<<','<<names[k]<<','<<(ready?"ready":"deferred")<<','<<i<<','<<c.sources[i]<<','<<applicable<<','<<r.metrics.certificate_applied<<','<<r.metrics.fallback<<','<<r.metrics.inspected_edges<<','<<p.old_reads<<','<<p.future_skips<<','<<p.outside_skips<<'\n';
  outputs.push_back(std::move(r.output));
 }
 st.queries=ns(queries);auto rel=Clock::now();m->release();lib.destroy(m);st.module_release=ns(rel);st.service=ns(start);
 auto validation=Clock::now();
 for(U i=0;i<=q;++i){auto&o=outputs[i];need(o&&o->graph().get()==c.graph.get()&&o->source()==c.sources[i]&&o->distance()==c.expected[i],"full distance / owned lifetime");++st.arrays;
  if(dump&&(i==0||i==1||i==2||i==q)){*dump<<"{\"graph\":\""<<c.name<<"\",\"file\":\""<<c.file<<"\",\"n\":"<<c.n<<",\"schedule\":\""<<c.schedule<<"\",\"mode\":\""<<names[k]<<"\",\"source\":"<<c.sources[i]<<",\"distance\":[";for(U j=0;j<c.n;++j){if(j)*dump<<',';*dump<<o->distance()[j];}*dump<<"]}\n";}
 }
 st.validation=ns(validation);rel=Clock::now();std::vector<Result>().swap(outputs);st.release=ns(rel);st.service+=st.release;st.lifecycle=ns(life);return st;
}
static void contract(){L tests=0;
 auto g=Graph::from_edges("contract",1,7,{{0,1},{0,1},{1,2},{2,0},{2,3},{5,6}});
 auto check=[&](bool v){need(v,"extended contract");++tests;};
 for(unsigned p=0;p<2;++p)for(unsigned k=9;k<=12;++k){auto&l=libraries[p][k];auto*m=l.create(API_VERSION);check(m!=nullptr);
  check(m->run({g,0}).status==Status::NOT_PREPARED);check(m->prepare(g,{},0).status==Status::OK);check(m->can_apply(g,1));
  auto held=m->run({g,1}).output;check(held&&held->distance()==oracle(*g,1));
  auto other=Graph::from_edges("contract",1,7,{{0,1}});check(!m->can_apply(other,1));check(m->run({other,1}).status==Status::INVALID_GRAPH);
  auto version=Graph::from_edges("contract",2,7,{{0,1}});check(m->run({version,1}).status==Status::INVALID_GRAPH);
  Request r{g,5};r.fail_output_allocation=true;check(m->run(r).status==Status::ALLOCATION_FAILED);check(m->can_apply(g,1)&&!m->can_apply(g,5));
  r={g,5};r.cancelled=true;check(m->run(r).status==Status::CANCELLED);check(m->can_apply(g,1));
  r={g,0};r.row_budget=1;auto partial=m->run(r);check(partial.status==Status::CANCELLED&&!partial.output);check(m->can_apply(g,1));
  r={g,5};r.row_budget=100;auto fallback=m->run(r);check(fallback.status==Status::OK&&fallback.metrics.fallback&&!fallback.metrics.certificate_applied&&fallback.output->distance()==oracle(*g,5));
  m->invalidate();check(!m->can_apply(g,1));check(m->update({g,0}).status==Status::OK&&m->can_apply(g,1));
  Request disabled{g,1};disabled.enabled=false;auto dr=m->run(disabled);check(dr.status==Status::OK&&dr.metrics.fallback&&dr.output->distance()==oracle(*g,1));
  m->release();l.destroy(m);check(held->distance()==oracle(*g,1));
  // All-n closure is deliberately ineligible under API 1.0.0 useful-bound semantics.
  auto all=Graph::from_edges("all",1,3,{{0,1},{1,2},{2,0}});m=l.create(API_VERSION);check(m->prepare(all,{},0).status==Status::OK);check(!m->can_apply(all,1));auto a=m->run({all,1});check(a.status==Status::OK&&a.metrics.fallback&&!a.metrics.certificate_applied&&a.output->distance()==oracle(*all,1));l.destroy(m);
 }
 std::cout<<"{\"status\":\"PASS\",\"extended_checks\":"<<tests<<"}\n";
}
static void diagnose(const std::string&out){auto all=cases(false);std::ofstream dump(out+"/arrays.jsonl"),work(out+"/work.csv");need(bool(dump)&&bool(work),"diagnose files");
 work<<"graph,schedule,mode,path,query,source,can_apply,certificate_applied,fallback,edges,old_reads,future_skips,outside_skips\n";L count=0;
 for(const auto&c:all)for(unsigned k=0;k<14;++k)for(bool ready:{false,true})count+=service(c,k,ready,32,&dump,&work).arrays;
 std::cout<<"{\"status\":\"PASS\",\"full_arrays\":"<<count<<",\"exported_arrays\":2688}\n";
}
static void worker(unsigned session,const std::string&out,bool phase){need(session<5,"session");auto all=cases(true);std::ofstream f(out);need(bool(f),"csv");f<<std::setprecision(17);
 f<<"session,round,sweep,order_index,graph,schedule,q,path,mode,service_ns,prepare_ns,queries_ns,historical_prepare_ns,validation_ns,release_ns,lifecycle_ns,module_release_ns,algorithm_ns,allocation_ns,copy_ns,maintenance_ns,lazy_reverse_ns,internal_run_ns,prepare_graph_ns,prepare_reverse_ns,prepare_workspace_ns,cache_bytes,adapter_csr_bytes,copy_elements,edges,edge_available,old_reads,future_skips,outside_skips,certificates,fallbacks,arrays\n";L trials=0,arrays=0;
 for(unsigned round=0;round<(phase?3:8);++round)for(const auto&c:all)for(U q:{8,32}){if(phase&&q!=32)continue;for(bool ready:{false,true}){
  std::vector<unsigned>order;for(unsigned i=0;i<14;++i)order.push_back((i+round+session)%14);if((round+session)%2)std::reverse(order.begin(),order.end());
  for(unsigned sweep=0;sweep<2;++sweep){if(sweep)std::reverse(order.begin(),order.end());for(unsigned j=0;j<order.size();++j){unsigned k=order[j];auto z=service(c,k,ready,q);
   f<<session<<','<<round<<','<<sweep<<','<<j<<','<<c.name<<','<<c.schedule<<','<<q<<','<<(ready?"ready":"deferred")<<','<<names[k]<<','<<z.service<<','<<z.prepare<<','<<z.queries<<','<<z.history<<','<<z.validation<<','<<z.release<<','<<z.lifecycle<<','<<z.module_release<<','<<z.algorithm<<','<<z.allocation<<','<<z.copy<<','<<z.maintenance<<','<<z.lazy_reverse<<','<<z.internal_run<<','<<z.prep_graph<<','<<z.prep_reverse<<','<<z.prep_workspace<<','<<z.cache<<','<<z.csr<<','<<z.copies<<','<<z.edges<<','<<z.edge_available<<','<<z.old_reads<<','<<z.future_skips<<','<<z.outside_skips<<','<<z.certificates<<','<<z.fallbacks<<','<<z.arrays<<'\n';++trials;arrays+=z.arrays;
  }}
 }}f.flush();need(bool(f),"csv write");rusage u{};getrusage(RUSAGE_SELF,&u);std::cout<<"{\"status\":\"PASS\",\"trials\":"<<trials<<",\"arrays\":"<<arrays<<",\"rss_peak_kib\":"<<u.ru_maxrss<<"}\n";
}
int main(int argc,char**argv){try{need(argc>=2,"command");std::string cmd=argv[1];double open=open_libraries(cmd=="phase");
 if(cmd=="contract")contract();else if(cmd=="diagnose"){need(argc==3,"output");diagnose(argv[2]);}else{need(argc==4,"worker arguments");worker(std::stoul(argv[2]),argv[3],cmd=="phase");}
 std::cerr<<"dlopen_startup_ns="<<open<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 2;}}
