#include "adapter.hpp"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <random>
#include <thread>
#include <set>
#include <sys/resource.h>
using namespace merged;
using Clock=std::chrono::steady_clock;
double ns(Clock::time_point s){return std::chrono::duration<double,std::nano>(Clock::now()-s).count();}
struct Case{std::string name,schedule,file;U n;std::vector<U>sources;std::shared_ptr<const Graph>g;std::shared_ptr<const Reverse>r;std::vector<std::vector<int>>expected;};
std::vector<Case>load(){
 std::ifstream f("fixtures/cases.txt");std::string line;std::vector<Case>v;
 while(std::getline(f,line)){std::istringstream ss(line);Case c;ss>>c.name>>c.schedule>>c.file>>c.n;U s;while(ss>>s)c.sources.push_back(s);
 c.g=Graph::load("fixtures/"+c.file,c.n,20261021);c.r=build(c.g);for(U s:c.sources)c.expected.push_back(oracle(*c.g,s));v.push_back(std::move(c));}return v;
}
L checks=0,comparisons=0;
void check(bool b,const char*msg){++checks;require(b,msg);}
void eq(const std::vector<int>&a,const std::vector<int>&b){++comparisons;check(a==b,"distance mismatch");}
void small_tests(){
 std::mt19937 rng(20261021);
 for(U gi=0;gi<576;++gi){
  U n=gi<512?3:1+rng()%48;std::vector<std::pair<U,U>>edges;
  if(gi<512){for(U u=0;u<3;++u)for(U v=0;v<3;++v)if(gi&(1<<(u*3+v)))edges.emplace_back(u,v);}
  else for(U j=0,k=rng()%300;j<k;++j)edges.emplace_back(rng()%n,rng()%n);
  auto g=std::make_shared<const Graph>(n,1,edges);auto r=build(g);std::vector<std::vector<int>>truth;for(U s=0;s<n;++s)truth.push_back(oracle(*g,s));
  for(auto m:modes()){Executor ex(g,r,m);consumer::Workspace w(n);Result retained;
   for(U qi=0;qi<12;++qi){U s=rng()%n;
    for(U t=0;t<n;++t){U count=0;for(int x:truth[t])count+=x>=0;check(ex.bound(t)>=count,"certificate inequality");}
    auto [o,st]=ex.run<true>(s,w);check(st.complete&&bool(o),"complete");eq(o->distance(),truth[s]);
    if(!retained)retained=o;else eq(retained->distance(),truth[retained->source()]);
   }
   ex.reset();check(ex.bound(0)==(m.wcc?ex.bound(0):n),"reset bound");
  }
 }
 auto g=std::make_shared<const Graph>(4,7,std::vector<std::pair<U,U>>{{0,1},{1,2},{2,3},{2,2},{1,2}});
 auto other=std::make_shared<const Graph>(4,7,std::vector<std::pair<U,U>>{{3,0}});
 auto r=build(g);auto ro=build(other);
 for(auto m:modes()){
  consumer::Workspace w(4);Executor e(g,r,m);
  auto old=e.run<true>(0,w).first;U bound=e.bound(1);
  if(!m.legacy){auto partial=e.run<true>(1,w,0);check(!partial.first&&!partial.second.complete,"cancel publication");check(e.bound(1)==bound,"cancel changes certificate");}
  bool caught=false;try{e.run<true>(1,w,UINT64_MAX,true);}catch(const std::bad_alloc&){caught=true;}check(caught,"output allocation failure");check(e.bound(1)==bound,"allocation changed certificate");eq(old->distance(),oracle(*g,0));
  caught=false;try{e.run(4,w);}catch(...){caught=true;}check(caught,"invalid source");
  caught=false;try{e.bind_reverse(ro);}catch(...){caught=true;}check(caught,"same version different identity");
  Executor low(g,r,m,0),fail(g,r,m,UINT64_MAX,true);
  eq(low.run(0,w).first->distance(),oracle(*g,0));eq(fail.run(0,w).first->distance(),oracle(*g,0));
 }
 Result retained;{Executor ex(g,r,mode("DO_RIE_RCC_LAST"));consumer::Workspace w(4);retained=ex.run(0,w).first;}eq(retained->distance(),oracle(*g,0));
}
void diagnose(std::vector<Case>&cases){
 std::ofstream f("results/work.csv"),out("results/distances.jsonl");
 f<<"graph,schedule,query,source,mode,edges,vertex_tests,levels,rows,bitmap_clear,bitmap_set,seen,bound,remaining,reason,table_scan,table_write,stop_checks,output_copy,reuse_hits,cache_payload,workspace_payload,graph_payload,reverse_payload\n";
 for(auto&c:cases)for(auto m:modes()){
  Executor ex(c.g,c.r,m);consumer::Workspace w(c.n,!m.push);
  for(U i=0;i<c.sources.size();++i){auto[o,t]=ex.run<true>(c.sources[i],w);eq(o->distance(),c.expected[i]);
   f<<c.name<<','<<c.schedule<<','<<i<<','<<c.sources[i]<<','<<m.name<<','<<t.edges<<','<<t.vertex_tests<<','<<t.levels<<','<<t.expanded_rows<<','<<t.bitmap_clear<<','<<t.bitmap_set<<','<<t.seen<<','<<t.limit<<','<<t.remaining_in<<','<<t.reason<<','<<t.publish_visits<<','<<t.publish_writes<<','<<t.stop_checks<<','<<t.return_copy<<','<<t.reuse_hits<<','<<ex.cache_bytes()<<','<<w.bytes()<<','<<c.g->payload_bytes()<<','<<(!m.push?c.r->payload_bytes():0)<<'\n';
   if(i==0||i==1||i==2||i==32){out<<"{\"graph\":\""<<c.name<<"\",\"schedule\":\""<<c.schedule<<"\",\"mode\":\""<<m.name<<"\",\"source\":"<<c.sources[i]<<",\"distance\":[";
    for(U j=0;j<c.n;++j){if(j)out<<',';out<<o->distance()[j];}out<<"]}\n";}
  }
 }
}
struct Batch{double elapsed=0,priming=0,validation=0,release=0;L cache=0,unique_outputs=0;};
Batch batch(Case&c,Mode m,bool warm){
 consumer::Workspace w(c.n,!m.push);std::vector<Result>outputs,history;outputs.reserve(33);history.reserve(3);
 Batch b;std::unique_ptr<Executor>ex;Clock::time_point t;
 if(warm){t=Clock::now();ex=std::make_unique<Executor>(c.g,c.r,m);for(U i=0;i<3;++i)history.push_back(ex->run(c.sources[i],w).first);b.priming=ns(t);}
 t=Clock::now();if(!ex)ex=std::make_unique<Executor>(c.g,c.r,m);
 for(U s:c.sources)outputs.push_back(ex->run(s,w).first);
 b.cache=ex->cache_bytes();ex.reset();b.elapsed=ns(t);
 t=Clock::now();for(U i=0;i<33;++i)eq(outputs[i]->distance(),c.expected[i]);for(U i=0;i<history.size();++i)eq(history[i]->distance(),c.expected[i]);b.validation=ns(t);
 std::set<const Output*>ids;for(auto&o:outputs)ids.insert(o.get());for(auto&o:history)ids.insert(o.get());b.unique_outputs=ids.size();
 t=Clock::now();outputs.clear();history.clear();b.release=ns(t);return b;
}
void gate(std::vector<Case>&cases,int session){
 std::ofstream f("results/gate_"+std::to_string(session)+".csv");f<<std::setprecision(17);
 f<<"session,round,graph,schedule,certificate,mode,q,ns,priming_ns,validation_ns,release_ns,cache_bytes,unique_output_bytes\n";
 for(int round=0;round<7;++round)for(auto&c:cases)for(int warm=0;warm<2;++warm){
  for(U mi=0;mi<modes().size();++mi){U j=(mi+round+session)%modes().size();if((session+round)%2)j=modes().size()-1-j;auto m=modes()[j];
   auto b=batch(c,m,warm);f<<session<<','<<round<<','<<c.name<<','<<c.schedule<<','<<(warm?"warm":"cold")<<','<<m.name<<",32,"<<b.elapsed<<','<<b.priming<<','<<b.validation<<','<<b.release<<','<<b.cache<<','<<b.unique_outputs*4*c.n<<'\n';
  }
 }f.flush();
}
struct Service{double total=0,a_compute=0,a_done=0,b_ready=0,prior=0,validation=0,release=0;L memory=0;bool b_before_a=false;};
Service service(Case&c,Mode m,const std::string&path,U q){
 Service st;std::shared_ptr<const Reverse>r;std::shared_ptr<Account>account;std::unique_ptr<Builder>builder;
 if(path=="ready"){auto t=Clock::now();r=build(c.g);st.prior=ns(t);}
 std::vector<Result>out;out.reserve(q+1);std::exception_ptr error;std::thread worker;std::atomic<bool>done{false};
 auto t=Clock::now();
 consumer::Workspace w(c.n,!m.push); // real workspace allocation is charged
 Executor ex(c.g,r,m,32ULL<<20,false,!m.push);
 if(path=="concurrent"){
  account=std::make_shared<Account>(32ULL<<20);builder=std::make_unique<Builder>(c.g,account);
  worker=std::thread([&]{try{builder->finish();r=builder->take();}catch(...){error=std::current_exception();}done.store(true,std::memory_order_release);});
 }
 try{
  out.push_back(ex.run_a(c.sources[0],w,st.a_compute).first);st.a_done=ns(t);st.b_before_a=done.load(std::memory_order_acquire)||path=="ready";
  if(path=="deferred"){account=std::make_shared<Account>(32ULL<<20);builder=std::make_unique<Builder>(c.g,account);builder->finish();r=builder->take();}
  if(worker.joinable())worker.join();if(error)std::rethrow_exception(error);
  if(!m.push){ex.bind_reverse(r);st.b_ready=ns(t);}
  for(U i=1;i<=q;++i)out.push_back(ex.run(c.sources[i],w).first);
  st.total=ns(t);
 }catch(...){if(builder)builder->cancel();if(worker.joinable())worker.join();throw;}
 // Conservative peak: all outputs plus all builder scratch, even if lifetimes
 // do not overlap. Graph transfer/loading is separate; payload only.
 st.memory=c.g->payload_bytes()+w.bytes()+ex.cache_bytes()+4ULL*c.n*(q+2)+(!m.push?full_build_payload(*c.g,false):0);
 require(st.memory<=(32ULL<<20),"service memory cap");
 t=Clock::now();for(U i=0;i<=q;++i)eq(out[i]->distance(),c.expected[i]);st.validation=ns(t);
 t=Clock::now();out.clear();st.release=ns(t);return st;
}
void service_phase(std::vector<Case>&cases,int session){
 std::ifstream allow("config/service_modes.txt");std::set<std::pair<std::string,std::string>>eligible;std::string a,b;while(allow>>a>>b)eligible.emplace(a,b);
 std::ofstream f("results/service_"+std::to_string(session)+".csv");f<<std::setprecision(17);
 f<<"session,round,graph,mode,path,q,total_ns,a_compute_ns,a_completion_ns,b_ready_ns,historical_prepare_ns,validation_ns,release_ns,payload_upper_bytes,b_ready_before_a\n";
 for(int round=0;round<7;++round)for(auto&c:cases)if(c.schedule=="original")for(U q:{0,1,2,8,32}){
  std::vector<std::pair<Mode,std::string>>paths;
  for(auto name:{"PUSH_N","PUSH_WCC","LAST_RESULT_REUSE"})paths.emplace_back(mode(name),"csr");
  for(auto m:modes())if(eligible.count({c.name,m.name})){
   if(m.push)paths.emplace_back(m,"csr");
   else for(auto p:{"deferred","concurrent","ready"})paths.emplace_back(m,p);
  }
  if((session+round)%2)std::reverse(paths.begin(),paths.end());
  for(auto [m,path]:paths){auto z=service(c,m,path,q);
   f<<session<<','<<round<<','<<c.name<<','<<m.name<<','<<path<<','<<q<<','<<z.total<<','<<z.a_compute<<','<<z.a_done<<','<<z.b_ready<<','<<z.prior<<','<<z.validation<<','<<z.release<<','<<z.memory<<','<<z.b_before_a<<'\n';}
 }f.flush();
}
int main(int argc,char**argv){
 try{
  require(argc>=2,"command");std::string command=argv[1];auto cases=load();
  if(command=="test"){
   small_tests();diagnose(cases);std::ofstream f("results/correctness.json");
   f<<"{\"status\":\"PASS\",\"graphs_small\":576,\"comparisons\":"<<comparisons<<",\"assertions\":"<<checks<<",\"fixture_requests\":"<<cases.size()*33*modes().size()<<"}\n";
   std::cout<<"PASS "<<checks<<" assertions "<<comparisons<<" comparisons\n";
  }else if(command=="worker"){
   require(argc==3,"session");int session=std::stoi(argv[2]);std::cout<<"READY\n"<<std::flush;
   std::string line;while(std::getline(std::cin,line)){if(line=="GATE"){gate(cases,session);std::cout<<"GATE_DONE\n"<<std::flush;}else if(line=="SERVICE"){service_phase(cases,session);std::cout<<"SERVICE_DONE\n"<<std::flush;}else if(line=="QUIT")break;else throw std::runtime_error("worker command");}
   rusage ru{};getrusage(RUSAGE_SELF,&ru);std::ofstream f("results/worker_"+std::to_string(session)+".json");
   f<<"{\"comparisons\":"<<comparisons<<",\"rss_peak_kib\":"<<ru.ru_maxrss<<"}\n";
  }else throw std::runtime_error("command");
  return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 2;}
}
