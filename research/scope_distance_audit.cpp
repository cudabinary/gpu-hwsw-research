// Isolated audit harness. Package headers and default RCC/API are unmodified.
#include "distance_guard.hpp"
#include <chrono>
#include <deque>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <sys/resource.h>
using namespace independent;
using Clock=std::chrono::steady_clock;
static double ns(Clock::time_point t){return std::chrono::duration<double,std::nano>(Clock::now()-t).count();}
static const std::string package="intake/rcc_scope_distance_20261021/package/RCC_SCOPE_CPU_MODULE_20261021";
static const std::vector<std::string>names={"PUSH_N","PUSH_RCC_TABLE","PUSH_RCC_LAST","OLD_P2","DO_RIE","DO_RIE_RCC_TABLE","SCOPE_COUNT","SCOPE_GLOBAL","SCOPE_LOCAL","SCOPE_COMPACT","DO_COMPACT","WCC_SCOPE","DIST_COUNT","DIST_CLOSURE","DIST_RADIUS","DIST_FRONTIER"};
static std::vector<int> oracle(const Graph&g,U s){
 std::vector<int>d(g.n(),-1);d[s]=0;std::deque<U>q{s};
 while(!q.empty()){auto u=q.front();q.pop_front();for(L e=g.row()[u];e<g.row()[u+1];++e){auto v=g.col()[e];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;
}
static auto build(std::shared_ptr<const Graph>g){auto a=std::make_shared<Account>(32ULL<<20);Builder b(g,a);b.finish();return b.take();}
struct Owned {
 std::shared_ptr<const Graph>graph;U source;std::vector<int>distance;
 Owned(std::shared_ptr<const Graph>g,U s):graph(std::move(g)),source(s),distance(graph->n()){}
};
using Result=std::shared_ptr<const Owned>;
class Runner {
 std::shared_ptr<const Graph>g_;std::shared_ptr<const Reverse>r_;unsigned kind_;
 std::unique_ptr<stop_bridge::Executor>old_;
 std::unique_ptr<rcc_scope::Executor>scope_;
 std::unique_ptr<rcc_scope::DistanceExecutor>distance_;
 std::unique_ptr<rcc_scope::WeakComponents>wcc_;
 std::vector<U>pending_;
 Result last_;U last_seen_=0;
public:
 consumer::Workspace w;
 Runner(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,unsigned k):g_(std::move(g)),r_(std::move(r)),kind_(k),w(g_->n(),k>=3){
  require(k<names.size(),"kind");
  if(k>=3)require(r_&&r_->graph_ptr().get()==g_.get(),"reverse identity");
  if(k==0||k==1||k==4||k==5){
   for(auto m:stop_bridge::modes())if(names[k]==m.name)old_=std::make_unique<stop_bridge::Executor>(g_,r_,m);
  }else if(k==2)old_=std::make_unique<stop_bridge::Executor>(g_,r_,stop_bridge::Mode{"PUSH_RCC_LAST",true,stop_bridge::N|stop_bridge::RCC,stop_bridge::Cache::LAST});
  else if(k>=6&&k<=10){
   auto type=k==6?rcc_scope::Kind::COUNT_ONLY:k==7?rcc_scope::Kind::SCOPE_GLOBAL:k==8?rcc_scope::Kind::SCOPE_LOCAL:k==9?rcc_scope::Kind::SCOPE_LOCAL_COMPACT:rcc_scope::Kind::DO_COMPACT;
   scope_=std::make_unique<rcc_scope::Executor>(g_,r_,type,32ULL<<20);
  }else if(k==11)wcc_=std::make_unique<rcc_scope::WeakComponents>(g_);
  else if(k>=12)distance_=std::make_unique<rcc_scope::DistanceExecutor>(g_,r_,rcc_scope::Guard(k-12),32ULL<<20);
 }
 L cache_bytes()const{return (old_?old_->cache_bytes():0)+(scope_?scope_->bytes():0)+(distance_?distance_->bytes():0)+(wcc_?wcc_->bytes():0)+4ULL*pending_.capacity();}
 template<bool D=false>std::pair<Result,rcc_scope::DistanceWork>run(U s){
  require(s<g_->n(),"source");rcc_scope::DistanceWork st;
  // Conventional immediate exact-result reuse is shared by every comparator.
  if(last_&&last_->source==s){st.complete=true;st.stop_reason=5;st.seen=last_seen_;return {last_,st};}
  // Reserve final owned output before any completed-result certificate publish.
  auto output=std::make_shared<Owned>(g_,s);
  if(old_){auto t=old_->run<D>(s,w);st.complete=t.complete;st.seen=t.seen;st.edges=t.edges;st.vertex_tests=t.vertex_tests;st.levels=t.levels;st.domain_size=t.limit;st.publish_tests=t.publish_visits;st.publish_writes=t.publish_writes;st.stop_reason=t.reason;}
  else if(kind_==3){
   if constexpr(D){auto t=consumer::diagnose(consumer::Mode::DIRECTION,*g_,*r_,s,w);for(auto l:t.levels){st.edges+=l.csr_edges+l.reverse_edges;st.vertex_tests+=l.unvisited_vertex_tests;}st.levels=t.levels.size();}
   else consumer::function(consumer::Mode::DIRECTION)(*g_,r_.get(),s,w);
   st.complete=true;if constexpr(D)st.seen=std::count_if(w.base.distance.begin(),w.base.distance.end(),[](int x){return x>=0;});
  }else if(scope_){static_cast<rcc_scope::Work&>(st)=scope_->run<D>(s,w);}
  else if(distance_)st=distance_->run<D>(s,w);
  else {auto d=wcc_->view(s);static_cast<rcc_scope::Work&>(st)=rcc_scope::direction<D>(*g_,*r_,s,w,d,{false,true,true},pending_);}
  require(st.complete,"incomplete result");
  const auto&d=old_?old_->output(w):distance_?distance_->output(w):w.base.distance;
  std::copy(d.begin(),d.end(),output->distance.begin());
  last_=std::move(output);last_seen_=st.seen;
  st.cache_live_bytes=cache_bytes();return {last_,st};
 }
};
struct Case{std::string name,file,schedule;U n;std::vector<U>sources;std::shared_ptr<const Graph>graph;std::vector<std::vector<int>>expected;};
static auto load(bool timing){
 std::vector<Case>cases;
 for(std::string schedule:{"legacy","unique"}){
  std::ifstream in(package+"/fixtures/scope_cases_"+schedule+".txt");require(bool(in),"cases open");std::string line;
  while(std::getline(in,line)){
   Case c;c.schedule=schedule;std::istringstream row(line);row>>c.name>>c.file>>c.n;
   if(timing&&c.name!="google_sampled_1024"&&c.name!="livejournal_sampled_4096"&&c.name!="lj_permuted"&&c.name!="scc4_d32"&&c.name!="oneway_dense")continue;
   U s;while(row>>s)c.sources.push_back(s);require(c.sources.size()==33,"33 sources");
   c.graph=Graph::load(package+"/fixtures/"+c.file,c.n,20261021);
   for(auto source:c.sources){c.expected.push_back(oracle(*c.graph,source));}
   cases.push_back(std::move(c));
  }
 }
 require(cases.size()==(timing?10:24),"case count");return cases;
}
static void arrays(std::ostream&f,const Case&c,unsigned k,U qi,const Result&o){
 f<<"{\"graph\":\""<<c.name<<"\",\"file\":\""<<c.file<<"\",\"n\":"<<c.n<<",\"schedule\":\""<<c.schedule<<"\",\"mode\":\""<<names[k]<<"\",\"source\":"<<c.sources[qi]<<",\"distance\":[";
 for(U j=0;j<c.n;++j){if(j)f<<',';f<<o->distance[j];}f<<"]}\n";
}
static void diagnose(const std::string&out){
 auto cases=load(false);std::ofstream work(out+"/work.csv"),dump(out+"/arrays.jsonl");
 require(bool(work)&&bool(dump),"diagnose output");
 work<<"graph,schedule,mode,query,source,edges,vertex_tests,levels,seen,domain,publish_tests,publish_writes,closure_skips,future_skips,old_distance_reads,cache_bytes,reused\n";
 L count=0,exports=0;
 for(const auto&c:cases){auto reverse=build(c.graph);for(unsigned k=0;k<names.size();++k){
  std::vector<Result>held;
  {Runner runner(c.graph,reverse,k);for(U i=0;i<33;++i){auto[o,st]=runner.run<true>(c.sources[i]);require(o->distance==c.expected[i],"diagnostic distance mismatch");held.push_back(o);++count;
    work<<c.name<<','<<c.schedule<<','<<names[k]<<','<<i<<','<<c.sources[i]<<','<<st.edges<<','<<st.vertex_tests<<','<<st.levels<<','<<st.seen<<','<<st.domain_size<<','<<st.publish_tests<<','<<st.publish_writes<<','<<st.outside_skips<<','<<st.future_level_skips<<','<<st.previous_distance_reads<<','<<runner.cache_bytes()<<','<<(st.stop_reason==5)<<'\n';
    if(i==0||i==1||i==2||i==32){arrays(dump,c,k,i,o);++exports;}
  }}
  // Retained results must survive executor/cache/workspace destruction.
  for(U i=0;i<33;++i)require(held[i]->distance==c.expected[i]&&held[i]->graph.get()==c.graph.get(),"owned result lifetime");
 }}
 std::cout<<"{\"status\":\"PASS\",\"full_arrays\":"<<count<<",\"exported_arrays\":"<<exports<<"}\n";
}
struct Timing {double service=0,prepare=0,queries=0,history=0,validation=0,release=0,lifecycle=0;L payload=0,cache=0,arrays=0;};
static Timing service(const Case&c,unsigned k,bool ready,U q){
 Timing st;std::vector<Result>outputs;const auto life=Clock::now();
 {
  std::shared_ptr<const Reverse>reverse;
  if(ready&&k>=3){auto prep=Clock::now();reverse=build(c.graph);st.history=ns(prep);}
  const auto start=Clock::now();outputs.reserve(q+1);
  if(!ready&&k>=3)reverse=build(c.graph);
  {
   Runner runner(c.graph,reverse,k);st.prepare=ns(start);const auto queries=Clock::now();
   for(U i=0;i<=q;++i)outputs.push_back(runner.run(c.sources[i]).first);
   st.queries=ns(queries);st.cache=runner.cache_bytes();
   st.payload=c.graph->payload_bytes()+runner.w.bytes()+st.cache+4ULL*c.n*(q+2)+(k>=3?full_build_payload(*c.graph,false):0);
   require(st.payload<=(32ULL<<20),"payload cap");
  }
  reverse.reset();st.service=ns(start);
 }
 auto validation=Clock::now();
 for(U i=0;i<=q;++i){require(outputs[i]&&outputs[i]->source==c.sources[i]&&outputs[i]->graph.get()==c.graph.get()&&outputs[i]->distance==c.expected[i],"full service owned output mismatch");++st.arrays;}
 st.validation=ns(validation);auto release=Clock::now();outputs.clear();st.release=ns(release);st.lifecycle=ns(life);return st;
}
static void worker(unsigned session,const std::string&out){
 require(session<3,"session");auto cases=load(true);std::ofstream csv(out);require(bool(csv),"service csv");csv<<std::setprecision(17);
 csv<<"session,round,sweep,order_index,graph,schedule,q,path,mode,service_ns,prepare_ns,queries_ns,historical_prepare_ns,validation_ns,release_ns,lifecycle_ns,cache_bytes,payload_upper_bytes,arrays\n";
 L trials=0,arrays=0;
 for(unsigned round=0;round<7;++round)for(const auto&c:cases)for(U q:{8,32})for(bool ready:{false,true}){
  std::vector<unsigned>order;for(unsigned i=0;i<names.size();++i)order.push_back((i+round+session)%names.size());
  if((round+session)%2)std::reverse(order.begin(),order.end());
  for(unsigned sweep=0;sweep<2;++sweep){if(sweep)std::reverse(order.begin(),order.end());for(unsigned j=0;j<order.size();++j){
   auto k=order[j];auto z=service(c,k,ready,q);
   csv<<session<<','<<round<<','<<sweep<<','<<j<<','<<c.name<<','<<c.schedule<<','<<q<<','<<(ready?"ready":"cold")<<','<<names[k]<<','<<z.service<<','<<z.prepare<<','<<z.queries<<','<<z.history<<','<<z.validation<<','<<z.release<<','<<z.lifecycle<<','<<z.cache<<','<<z.payload<<','<<z.arrays<<'\n';++trials;arrays+=z.arrays;
  }}
 }
 csv.flush();require(bool(csv),"csv write");rusage usage{};getrusage(RUSAGE_SELF,&usage);
 std::cout<<"{\"status\":\"PASS\",\"trials\":"<<trials<<",\"arrays\":"<<arrays<<",\"rss_peak_kib\":"<<usage.ru_maxrss<<"}\n";
}
int main(int argc,char**argv){try{
 require(argc>=3,"command output");if(std::string(argv[1])=="diagnose")diagnose(argv[2]);
 else {require(argc==4&&std::string(argv[1])=="worker","worker session csv");worker(std::stoul(argv[2]),argv[3]);}
 return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 2;}}
