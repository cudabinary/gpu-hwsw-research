#include "distance_guard.hpp"
#include <chrono>
#include <deque>
#include <fstream>
#include <sstream>
#include <iostream>
#include <random>
using namespace independent;using Clock=std::chrono::steady_clock;
static L checks=0;static void check(bool x,const char*m){++checks;if(!x)throw std::runtime_error(m);}
static std::vector<int>ref(const Graph&g,U s){std::vector<int>d(g.n(),-1);d[s]=0;std::deque<U>q{ s };while(!q.empty()){U u=q.front();q.pop_front();for(L e=g.row()[u];e<g.row()[u+1];++e){U v=g.col()[e];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;}
static auto build(std::shared_ptr<const Graph>g){auto a=std::make_shared<Account>(128ull<<20);Builder b(g,a);b.finish();return b.take();}
static const std::vector<std::string>names={"PUSH_N","PUSH_RCC_TABLE","DO_RIE","DO_RIE_RCC_TABLE","LAST_COUNT","LAST_CLOSURE","LAST_RADIUS","LAST_FRONTIER"};
class Run{std::unique_ptr<stop_bridge::Executor>old_;std::unique_ptr<rcc_scope::DistanceExecutor>guard_;U last_=0;bool valid_=false;rcc_scope::DistanceWork lastwork_;
public:consumer::Workspace w;
 Run(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,U mode):w(g->n(),mode>1){if(mode<4){for(auto&m:stop_bridge::modes())if(m.name==names[mode])old_=std::make_unique<stop_bridge::Executor>(g,r,m);}else guard_=std::make_unique<rcc_scope::DistanceExecutor>(g,r,rcc_scope::Guard(mode-4));}
 template<bool D=false>rcc_scope::DistanceWork run(U s){if(valid_&&last_==s){rcc_scope::DistanceWork a;a.complete=true;a.stop_reason=5;a.seen=lastwork_.seen;return a;}
 rcc_scope::DistanceWork a;if(guard_)a=guard_->run<D>(s,w);else{auto b=old_->run<D>(s,w);a.complete=b.complete;a.edges=b.edges;a.vertex_tests=b.vertex_tests;a.levels=b.levels;a.seen=b.seen;a.domain_size=b.limit;a.stop_reason=b.reason;a.publish_tests=b.publish_visits;a.publish_writes=b.publish_writes;}
 valid_=a.complete;last_=s;lastwork_=a;return a;}
 const std::vector<int>&output()const{return guard_?guard_->output(w):old_->output(w);}
 L bytes()const{return guard_?guard_->bytes():old_->cache_bytes();}
};
struct Case{std::string name,file,sch;U n;std::vector<U>seq;};
static auto cases(const std::string&dir){std::vector<Case>cs;for(auto sch:{"legacy","unique"}){std::ifstream f(dir+"/scope_cases_"+sch+".txt");require(bool(f),"cases");std::string l;while(std::getline(f,l)){std::istringstream is(l);Case c;c.sch=sch;is>>c.name>>c.file>>c.n;U s;while(is>>s)c.seq.push_back(s);require(c.seq.size()==33,"sources");cs.push_back(c);}}return cs;}
static void array(std::ostream&o,const std::vector<int>&d){o<<'[';for(std::size_t i=0;i<d.size();++i){if(i)o<<',';o<<d[i];}o<<']';}
static void test(){L count=0,graphs=0;std::mt19937 rng(4132021);
 auto one=[&](std::shared_ptr<const Graph>g){++graphs;auto r=build(g);std::vector<U>seq;for(U i=0;i<10;++i)seq.push_back(i<g->n()?i:rng()%g->n());std::vector<std::vector<int>>want;for(U s:seq)want.push_back(ref(*g,s));
 for(U m=0;m<8;++m){Run run(g,r,m);for(U j=0;j<seq.size();++j){auto a=run.run<true>(seq[j]);check(a.complete&&run.output()==want[j],"distance guard incorrect");++count;}}
 consumer::Workspace w0(g->n()),w1(g->n()),w2(g->n());rcc_scope::DistanceExecutor a(g,r,rcc_scope::Guard::COUNT_ONLY),b(g,r,rcc_scope::Guard::DISTANCE_RADIUS),c(g,r,rcc_scope::Guard::FRONTIER_MAX);
 for(U s:seq){auto x=a.run<true>(s,w0),y=b.run<true>(s,w1),z=c.run<true>(s,w2);check(a.output(w0)==b.output(w1)&&b.output(w1)==c.output(w2),"guard parity");check(x.levels==y.levels&&y.levels==z.levels&&y.edges<=x.edges&&z.edges<=y.edges,"guard work domination");}}
 ;for(U mask=0;mask<512;++mask){std::vector<std::pair<U,U>>e;for(U i=0;i<9;++i)if(mask&(1u<<i))e.emplace_back(i/3,i%3);one(std::make_shared<const Graph>(3,mask+1,e));}
 for(U j=0;j<128;++j){U n=1+rng()%100,m=rng()%1000;std::vector<std::pair<U,U>>e;for(U i=0;i<m;++i)e.emplace_back(rng()%n,rng()%n);one(std::make_shared<const Graph>(n,1000+j,e));}
 auto g=std::make_shared<const Graph>(4,1,std::vector<std::pair<U,U>>{{0,1},{1,2},{2,3}});auto r=build(g);consumer::Workspace w(4);rcc_scope::DistanceExecutor ex(g,r,rcc_scope::Guard::FRONTIER_MAX);ex.run(0,w);auto bound=ex.bound(1);auto a=ex.run(1,w,0);check(!a.complete&&ex.bound(1)==bound,"partial guard publication");ex.run(1,w);check(ex.output(w)==ref(*g,1),"abort recovery");
 rcc_scope::DistanceExecutor zero(g,r,rcc_scope::Guard::DISTANCE_RADIUS,0);zero.run(1,w);check(zero.bytes()==0&&zero.output(w)==ref(*g,1),"zero budget fallback");
 std::cout<<"{\"status\":\"PASS\",\"graphs\":"<<graphs<<",\"mode_query_comparisons\":"<<count<<",\"assertions\":"<<checks<<",\"GPU\":0}\n";
}
static void diagnose(const std::string&dir,const std::string&out){std::ofstream f(out+"/guard_work.csv"),ar(out+"/guard_arrays.jsonl");f<<"graph,schedule,mode,query,source,edges,vertex_tests,levels,closure_skips,future_skips,old_distance_reads,seen,stop_reason,bytes\n";L count=0,exports=0;
 for(auto&c:cases(dir)){auto g=Graph::load(dir+"/"+c.file,c.n,1);auto r=build(g);std::vector<std::vector<int>>want;for(U s:c.seq)want.push_back(ref(*g,s));
 for(U m=0;m<8;++m){Run run(g,r,m);for(U i=0;i<c.seq.size();++i){auto a=run.run<true>(c.seq[i]);check(a.complete&&run.output()==want[i],"guard fixture");++count;f<<c.name<<','<<c.sch<<','<<names[m]<<','<<i<<','<<c.seq[i]<<','<<a.edges<<','<<a.vertex_tests<<','<<a.levels<<','<<a.outside_skips<<','<<a.future_level_skips<<','<<a.previous_distance_reads<<','<<a.seen<<','<<a.stop_reason<<','<<run.bytes()<<'\n';
 if(i==0||i==1||i==2||i==32){++exports;ar<<"{\"graph\":\""<<c.name<<"\",\"file\":\""<<c.file<<"\",\"n\":"<<c.n<<",\"source\":"<<c.seq[i]<<",\"mode\":\""<<names[m]<<"\",\"distance\":";array(ar,run.output());ar<<"}\n";}}}}
 std::cout<<"{\"status\":\"PASS\",\"fixture_comparisons\":"<<count<<",\"exported_arrays\":"<<exports<<"}\n";
}
static void bench(const std::string&dir,U session){require(session<3,"3 process limit");volatile L sink=0;std::cout<<"graph,schedule,session,round,q,mode,elapsed_ns,cache_bytes,boundary\n";
 for(auto&c:cases(dir)){auto g=Graph::load(dir+"/"+c.file,c.n,1);auto r=build(g);std::vector<std::vector<int>>want;for(U s:c.seq)want.push_back(ref(*g,s));std::vector<int>history(L(c.n)*33);
 for(U round=0;round<7;++round)for(U turn=0;turn<8;++turn){U m=(turn+round+session)%8;L bytes=0;auto t=Clock::now();{
 Run run(g,r,m);for(U j=0;j<33;++j){auto a=run.run(c.seq[j]);require(a.complete,"guard incomplete timing");std::copy(run.output().begin(),run.output().end(),history.begin()+L(j)*c.n);}bytes=run.bytes();}
 auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t).count();for(U j=0;j<33;++j)check(std::equal(want[j].begin(),want[j].end(),history.begin()+L(j)*c.n),"guard timing output");sink+=U(history[0]);std::cout<<c.name<<','<<c.sch<<','<<session<<','<<round<<",32,"<<names[m]<<','<<elapsed<<','<<bytes<<",CPU_RESIDENT_REVERSE_COLD_DISTANCE_CACHE\n";}}
 std::cerr<<"{\"status\":\"PASS\",\"checks\":"<<checks<<",\"checksum\":"<<sink<<"}\n";
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="test")test();else if(argc==4&&std::string(argv[1])=="diagnose")diagnose(argv[2],argv[3]);else if(argc==4&&std::string(argv[1])=="bench")bench(argv[2],U(std::stoul(argv[3])));else throw std::runtime_error("usage: distance_probe test|diagnose FIX OUT|bench FIX SESSION");}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
