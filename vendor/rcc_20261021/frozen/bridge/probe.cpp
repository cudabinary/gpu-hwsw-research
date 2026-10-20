#include "stop_bridge.hpp"
#include <chrono>
#include <deque>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <numeric>
#include <iomanip>
using namespace independent;
using Clock=std::chrono::steady_clock;
static L checks=0;
static void check(bool b,const char*s){++checks;if(!b)throw std::runtime_error(s);}
static std::vector<int> reference(const Graph&g,U s){
    require(s<g.n(),"oracle source");std::vector<int>d(g.n(),-1);std::deque<U>q;d[s]=0;q.push_back(s);
    while(!q.empty()){U u=q.front();q.pop_front();for(L e=g.row()[u];e<g.row()[u+1];++e){U v=g.col()[e];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;
}
static auto build(std::shared_ptr<const Graph>g){auto a=std::make_shared<Account>(64ull<<20);Builder b(g,a,false);b.finish();return b.take();}
struct Case {std::string name,file,schedule;U n;std::vector<U>sources;};
static std::vector<Case>cases(const std::string&dir){std::vector<Case>v;
    for(auto schedule:{"original","holdout"}){std::ifstream f(dir+"/cases_"+schedule+".txt");require(bool(f),"case list");std::string l;
      while(std::getline(f,l)){if(l.empty())continue;std::istringstream s(l);Case c;c.schedule=schedule;s>>c.name>>c.file>>c.n;U x;while(s>>x)c.sources.push_back(x);require(c.sources.size()==33,"expected A+32 source sequence");v.push_back(c);}}
    return v;}
static void emit_array(std::ostream&o,const std::vector<int>&d){o<<'[';for(std::size_t i=0;i<d.size();++i){if(i)o<<',';o<<d[i];}o<<']';}
static void tests(){L graphs=0,queries=0,bounds=0,rie_stops=0,rcc_stops=0;std::mt19937 rng(20261021);
    auto one=[&](std::shared_ptr<const Graph>g){++graphs;auto r=build(g);std::vector<std::vector<int>>expect;std::vector<U>reach;
      for(U s=0;s<g->n();++s){expect.push_back(reference(*g,s));reach.push_back(U(std::count_if(expect.back().begin(),expect.back().end(),[](int x){return x>=0;})));}
      for(const auto&m:stop_bridge::modes()){stop_bridge::Executor ex(g,r,m);consumer::Workspace w(g->n());
        for(U j=0;j<12;++j){U s=(j<g->n()?j:rng()%g->n());auto st=ex.run<true>(s,w);++queries;
          check(st.complete&&ex.output(w)==expect[s],"new consumer distance mismatch");check(st.seen==reach[s],"wrong discovered count");rie_stops+=st.reason==2;rcc_stops+=st.reason==3;
          for(U v=0;v<g->n();++v){check(ex.bound(v)>=reach[v],"unsafe published bound");++bounds;}
        }
        ex.reset();for(U v=0;v<g->n();++v)check(ex.bound(v)==g->n(),"reset must drop certificate");
        auto old=ex.bounds();auto st=ex.run<true>(0,w,0);if(!st.complete)check(ex.bounds()==old,"partial publication");
        bool bad=false;try{ex.run(g->n(),w);}catch(const std::exception&){bad=true;}check(bad,"source rejection");
      }
      // The bridge's unoptimized Direction preserves the supplied policy work.
      consumer::Workspace w(g->n());for(U s=0;s<std::min<U>(4,g->n());++s){auto orig=consumer::diagnose(consumer::Mode::DIRECTION,*g,*r,s,w);L edges=0;for(auto&lv:orig.levels)edges+=lv.csr_edges+lv.reverse_edges;
        auto st=stop_bridge::direction<true>(*g,*r,s,w,0,g->n());check(st.edges==edges&&st.levels==orig.levels.size(),"unmodified policy work differs");}
    };
    for(U mask=0;mask<512;++mask){std::vector<std::pair<U,U>>e;for(U i=0;i<9;++i)if(mask&(1u<<i))e.emplace_back(i/3,i%3);one(std::make_shared<const Graph>(3,mask+1,e));}
    for(U k=0;k<96;++k){U n=1+rng()%48,m=rng()%300;std::vector<std::pair<U,U>>e;for(U i=0;i<m;++i)e.emplace_back(rng()%n,rng()%n);one(std::make_shared<const Graph>(n,1000+k,e));}
    auto g=std::make_shared<const Graph>(4,1,std::vector<std::pair<U,U>>{{0,1},{2,3},{3,2}});auto g2=std::make_shared<const Graph>(4,1,std::vector<std::pair<U,U>>{{0,2}});auto r=build(g);bool bad=false;
    try{stop_bridge::Executor ex(g2,r,stop_bridge::modes()[4]);}catch(const std::exception&){bad=true;}check(bad,"same numeric version different object rejected");
    std::cout<<"{\"status\":\"PASS\",\"graphs\":"<<graphs<<",\"mode_query_comparisons\":"<<queries<<",\"bound_inequalities\":"<<bounds<<",\"assertions\":"<<checks<<",\"RIE_stops\":"<<rie_stops<<",\"RCC_stops\":"<<rcc_stops<<",\"GPU_runs\":0,\"sanitizer_runs\":0}\n";
}
static void diagnose(const std::string&dir,const std::string&out){std::ofstream f(out+"/bridge_work.csv"),arr(out+"/bridge_arrays.jsonl");
    f<<"graph,schedule,mode,query_index,source,seen,bound,edges,levels,vertex_tests,remaining_in,stop_reason,publish_visits,publish_writes,extra_cache_bytes\n";
    L queries=0,exported=0;for(const auto&c:cases(dir)){auto g=Graph::load(dir+"/"+c.file,c.n,1);auto r=build(g);consumer::Workspace w(c.n);std::vector<std::vector<int>>expect;for(U s:c.sources)expect.push_back(reference(*g,s));
      for(const auto&m:stop_bridge::modes()){stop_bridge::Executor ex(g,r,m);
        for(U i=0;i<c.sources.size();++i){auto st=ex.run<true>(c.sources[i],w);check(st.complete&&ex.output(w)==expect[i],"fixture distance mismatch");++queries;
          f<<c.name<<','<<c.schedule<<','<<m.name<<','<<i<<','<<c.sources[i]<<','<<st.seen<<','<<st.limit<<','<<st.edges<<','<<st.levels<<','<<st.vertex_tests<<','<<st.remaining_in<<','<<st.reason<<','<<st.publish_visits<<','<<st.publish_writes<<','<<ex.cache_bytes()<<'\n';
          if(i==0||i==1||i==2||i==32){++exported;arr<<"{\"graph\":\""<<c.name<<"\",\"file\":\""<<c.file<<"\",\"n\":"<<c.n<<",\"schedule\":\""<<c.schedule<<"\",\"mode\":\""<<m.name<<"\",\"source\":"<<c.sources[i]<<",\"qindex\":"<<i<<",\"distance\":";emit_array(arr,ex.output(w));arr<<"}\n";}
        }
      }
    }
    std::cout<<"{\"status\":\"PASS\",\"fixture_mode_queries\":"<<queries<<",\"exported_arrays\":"<<exported<<",\"checks\":"<<checks<<"}\n";
}
static void bench(const std::string&dir,U session){require(session<3,"session limit");auto all=cases(dir);
    // Fixed full batch, cache cold but graph/reverse/workspace/history resident.
    // Includes certificate initialization, queries, updates, result copies,
    // destruction. Reverse construction and file I/O excluded, no cold-service claim.
    std::cout<<"graph,schedule,session,round,q,mode,elapsed_ns,cache_bytes,boundary,checksum\n";
    volatile L sink=0;const auto&mods=stop_bridge::modes();
    for(const auto&c:all){auto g=Graph::load(dir+"/"+c.file,c.n,1);auto r=build(g);consumer::Workspace w(c.n);
      std::vector<std::vector<int>>expect;for(U s:c.sources)expect.push_back(reference(*g,s));
      for(U q:{8u,32u}){std::vector<int>history(std::size_t(c.n)*(q+1));
        for(U round=0;round<7;++round)for(U turn=0;turn<mods.size()+2;++turn){U id=(turn+round+session)%(mods.size()+2);L extra=0;
          const auto t0=Clock::now();
          if(id<mods.size()){
            stop_bridge::Executor ex(g,r,mods[id]);extra=ex.cache_bytes();
            for(U i=0;i<=q;++i){auto st=ex.run(c.sources[i],w);if(!st.complete)throw std::runtime_error("incomplete timed batch");std::copy(ex.output(w).begin(),ex.output(w).end(),history.begin()+L(i)*c.n);}
          }else{auto fn=consumer::function(id==mods.size()?consumer::Mode::QUEUE_PUSH:consumer::Mode::DIRECTION);
            for(U i=0;i<=q;++i){fn(*g,r.get(),c.sources[i],w);std::copy(w.base.distance.begin(),w.base.distance.end(),history.begin()+L(i)*c.n);}}
          const auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t0).count();
          for(U i=0;i<=q;++i)check(std::equal(expect[i].begin(),expect[i].end(),history.begin()+L(i)*c.n),"timed output mismatch");
          L checksum=0;for(U i=0;i<=q;++i)checksum+=U(history[L(i)*c.n+c.sources[i]])+i;sink+=checksum;
          std::cout<<c.name<<','<<c.schedule<<','<<session<<','<<round<<','<<q<<','<<(id<mods.size()?mods[id].name:(id==mods.size()?"PINNED_P0":"PINNED_P2"))<<','<<elapsed<<','<<extra<<",RESIDENT_REVERSE_COLD_CERT_"<<q+1<<"_REQUEST_BATCH,"<<checksum<<'\n';
        }
      }
    }
    std::cerr<<"{\"status\":\"PASS\",\"checks\":"<<checks<<",\"checksum\":"<<sink<<"}\n";
}
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="test")tests();
 else if(argc==4&&std::string(argv[1])=="diagnose")diagnose(argv[2],argv[3]);
 else if(argc==4&&std::string(argv[1])=="bench")bench(argv[2],U(std::stoul(argv[3])));
 else throw std::runtime_error("usage: probe test | diagnose FIXTURES OUTDIR | bench FIXTURES SESSION0..2");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
