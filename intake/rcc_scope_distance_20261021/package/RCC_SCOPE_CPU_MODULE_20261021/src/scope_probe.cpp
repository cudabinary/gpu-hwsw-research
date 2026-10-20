#include "closure_scope.hpp"
#include <chrono>
#include <deque>
#include <fstream>
#include <sstream>
#include <iostream>
#include <random>
#include <iomanip>
#include <set>
using namespace independent;
using Clock=std::chrono::steady_clock;
static L assertions=0;
static void check(bool p,const char*msg){++assertions;if(!p)throw std::runtime_error(msg);}
static std::vector<int> reference(const Graph&g,U s){
    require(s<g.n(),"ref source");std::vector<int>d(g.n(),-1);std::deque<U>q;d[s]=0;q.push_back(s);
    while(!q.empty()){U u=q.front();q.pop_front();for(L e=g.row()[u];e<g.row()[u+1];++e){U v=g.col()[e];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;
}
static std::shared_ptr<const Reverse> build(std::shared_ptr<const Graph>g){auto a=std::make_shared<Account>(128ull<<20);Builder b(g,a,false);b.finish();return b.take();}
struct Case{std::string name,file,schedule;U n;std::vector<U>sources;};
static std::vector<Case>cases(const std::string&dir){std::vector<Case>v;
    for(const auto&sch:{"legacy","unique"}){std::ifstream f(dir+"/scope_cases_"+sch+".txt");require(bool(f),"case list");std::string line;
        while(std::getline(f,line)){if(line.empty()||line[0]=='#')continue;std::istringstream ss(line);Case c;c.schedule=sch;ss>>c.name>>c.file>>c.n;U x;while(ss>>x)c.sources.push_back(x);require(c.sources.size()==33,"33 sources required");v.push_back(c);}}
    return v;
}
static const std::vector<std::string>modes={"PUSH_N","PUSH_RCC_TABLE","DO_RIE","DO_RIE_RCC_TABLE","DO_COMPACT","DO_CLOSURE_COUNT","DO_SCOPE_GLOBAL","DO_SCOPE_LOCAL","DO_SCOPE_COMPACT","DO_WCC_LOCAL","PUSH_WCC"};
class Runner{
    std::shared_ptr<const Graph>g_;std::shared_ptr<const Reverse>r_;std::string mode_;
    std::unique_ptr<stop_bridge::Executor>old_;std::unique_ptr<rcc_scope::Executor>sc_;
    std::unique_ptr<rcc_scope::WeakComponents>wcc_;std::vector<U>pending_;
    U last_=0;bool has_last_=false;rcc_scope::Work last_work_;
public:
    consumer::Workspace w;L identical_source_reuses=0;
    Runner(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,std::string mode):g_(std::move(g)),r_(std::move(r)),mode_(std::move(mode)),w(g_->n(),mode_.rfind("PUSH",0)!=0){
        if(mode_=="PUSH_N"||mode_=="PUSH_RCC_TABLE"||mode_=="DO_RIE"||mode_=="DO_RIE_RCC_TABLE"){
            for(auto&m:stop_bridge::modes())if(m.name==mode_){old_=std::make_unique<stop_bridge::Executor>(g_,r_,m);break;}}
        else if(mode_=="DO_WCC_LOCAL"||mode_=="PUSH_WCC")wcc_=std::make_unique<rcc_scope::WeakComponents>(g_);
        else{rcc_scope::Kind k=rcc_scope::Kind::COUNT_ONLY;
            if(mode_=="DO_SCOPE_GLOBAL")k=rcc_scope::Kind::SCOPE_GLOBAL;
            else if(mode_=="DO_SCOPE_LOCAL")k=rcc_scope::Kind::SCOPE_LOCAL;
            else if(mode_=="DO_SCOPE_COMPACT")k=rcc_scope::Kind::SCOPE_LOCAL_COMPACT;
            else if(mode_=="DO_COMPACT")k=rcc_scope::Kind::DO_COMPACT;
            else require(mode_=="DO_CLOSURE_COUNT","unknown mode");
            sc_=std::make_unique<rcc_scope::Executor>(g_,r_,k);}
        require(old_||sc_||wcc_,"runner init");
    }
    L bytes()const{return w.bytes()+(old_?old_->cache_bytes():0)+(sc_?sc_->bytes():0)+(wcc_?wcc_->bytes():0)+4*L(pending_.capacity());}
    L extra()const{return bytes()-w.bytes();}
    template<bool D=false>rcc_scope::Work run(U s){
        require(s<g_->n(),"runner source");
        if(has_last_&&s==last_){++identical_source_reuses;rcc_scope::Work a;a.complete=true;a.seen=last_work_.seen;a.domain_size=last_work_.domain_size;a.stop_reason=5;a.cache_live_bytes=extra();return a;}
        rcc_scope::Work a;
        if(old_){auto b=old_->run<D>(s,w);a.edges=b.edges;a.vertex_tests=b.vertex_tests;a.levels=b.levels;a.bitmap_clear=b.bitmap_clear;a.bitmap_set=b.bitmap_set;a.publish_tests=b.publish_visits;a.publish_writes=b.publish_writes;a.seen=b.seen;a.domain_size=b.limit;a.stop_reason=b.reason;a.remaining_global=b.remaining_in;a.complete=b.complete;}
        else if(sc_)a=sc_->run<D>(s,w);
        else if(mode_=="PUSH_WCC"){auto dom=wcc_->view(s);auto b=stop_bridge::push<D>(*g_,s,w,dom.size,true);a.edges=b.edges;a.seen=b.seen;a.domain_size=dom.size;a.complete=b.complete;a.stop_reason=b.reason;}
        else{auto dom=wcc_->view(s);a=rcc_scope::direction<D>(*g_,*r_,s,w,dom,{false,true,true},pending_);}
        a.cache_live_bytes=extra();has_last_=a.complete;last_=s;last_work_=a;return a;
    }
    const std::vector<int>&output()const{return old_?old_->output(w):w.base.distance;}
};
static void arr(std::ostream&o,const std::vector<int>&d){o<<'[';for(std::size_t i=0;i<d.size();++i){if(i)o<<',';o<<d[i];}o<<']';}
static void tests(){L graph_count=0,comparisons=0,scope_assertions=0;std::mt19937 gen(381021);
    auto one=[&](std::shared_ptr<const Graph>g){++graph_count;auto r=build(g);std::vector<U>sources;
        for(U i=0;i<8;++i){sources.push_back(i<g->n()?i:gen()%g->n());}std::vector<std::vector<int>>want;for(U s:sources)want.push_back(reference(*g,s));
        for(const auto&m:modes){Runner run(g,r,m);for(U i=0;i<sources.size();++i){auto w=run.run<true>(sources[i]);++comparisons;check(w.complete&&run.output()==want[i],"mode BFS mismatch");check(w.seen==U(std::count_if(want[i].begin(),want[i].end(),[](int v){return v>=0;})),"seen mismatch");}}
        rcc_scope::Executor ex(g,r,rcc_scope::Kind::SCOPE_LOCAL);consumer::Workspace w(g->n());
        for(U s:sources){ex.run<true>(s,w);auto c=ex.snapshot();if(c){L k=0;for(U u:c->vertices()){check(c->contains(u),"membership mismatch");k+=r->row()[u+1]-r->row()[u];for(L e=g->row()[u];e<g->row()[u+1];++e){check(c->contains(g->col()[e]),"not closed");++scope_assertions;}}check(k==c->incoming(),"regional incoming mass");}}
    };
    for(U mask=0;mask<512;++mask){std::vector<std::pair<U,U>>e;for(U i=0;i<9;++i)if(mask&(1u<<i))e.emplace_back(i/3,i%3);one(std::make_shared<const Graph>(3,mask+1,e));}
    for(U mask=0;mask<4096;++mask){std::vector<std::pair<U,U>>e;U b=0;for(U u=0;u<4;++u)for(U v=0;v<4;++v)if(u!=v){if(mask&(1u<<b))e.emplace_back(u,v);++b;}one(std::make_shared<const Graph>(4,1000+mask,e));}
    for(U i=0;i<128;++i){U n=1+gen()%80,m=gen()%1200;std::vector<std::pair<U,U>>e;for(U j=0;j<m;++j)e.emplace_back(gen()%n,gen()%n);one(std::make_shared<const Graph>(n,10000+i,e));}
    auto g=std::make_shared<const Graph>(6,1,std::vector<std::pair<U,U>>{{0,1},{1,2},{2,1},{3,1},{3,4},{4,3}});auto r=build(g);consumer::Workspace w(6);
    rcc_scope::Executor ex(g,r,rcc_scope::Kind::SCOPE_LOCAL);ex.run<true>(1,w);auto c=ex.snapshot();check(c&&c->size()==2,"small closure expected");
    auto abort=ex.run<true>(3,w,0);check(!abort.complete&&ex.snapshot()==c,"abort published");
    ex.fail_next_publication();auto result=ex.run<true>(3,w);check(result.complete&&result.allocation_refused&&ex.snapshot()==c&&w.base.distance==reference(*g,3),"allocation failure damaged state");
    ex.run<true>(3,w);check(ex.snapshot()!=c&&c->contains(1)&&!c->contains(3),"old immutable reader");ex.reset();check(!ex.snapshot(),"reset");
    rcc_scope::Executor capped(g,r,rcc_scope::Kind::SCOPE_LOCAL,0);auto z=capped.run<true>(1,w);check(z.allocation_refused&&!capped.snapshot()&&w.base.distance==reference(*g,1),"budget fallback");
    auto other=std::make_shared<const Graph>(6,1,std::vector<std::pair<U,U>>{{1,5}});bool rejected=false;
    try{rcc_scope::Executor bad(other,r,rcc_scope::Kind::SCOPE_LOCAL);}catch(const std::exception&){rejected=true;}check(rejected,"graph identity reuse");
    rejected=false;try{ex.run(6,w);}catch(const std::exception&){rejected=true;}check(rejected,"invalid source");
    // Minimal directed incoming-bound counterexample: R={1,2}, 0->1 enters R.
    auto ig=std::make_shared<const Graph>(3,2,std::vector<std::pair<U,U>>{{0,1},{1,2}});auto ir=build(ig);consumer::Workspace iw(3);rcc_scope::Executor ix(ig,ir,rcc_scope::Kind::SCOPE_LOCAL);
    ix.run<true>(1,iw);check(ix.snapshot()->incoming()==2,"external incoming edge must be retained in mass");ix.run<true>(2,iw);check(iw.base.distance==reference(*ig,2),"strict subset scope");
    // Incomplete prefix {0,1} of 0->1->2 is not a closure: no publication allowed.
    rcc_scope::Executor px(ig,ir,rcc_scope::Kind::SCOPE_LOCAL);auto p=px.run<true>(0,iw,1);check(!p.complete&&!px.snapshot(),"partial search incorrectly certified");
    // Count-only and scope-global have identical level sequence/termination,
    // but pruning can only reduce reverse probes and vertex checks.
    for(U rep=0;rep<16;++rep){std::vector<std::pair<U,U>>e;for(U i=0;i<128;++i){U u=gen()%16,v=gen()%16;if(u/8==v/8)e.emplace_back(u,v);}auto cg=std::make_shared<const Graph>(16,rep+1,e);auto cr=build(cg);consumer::Workspace wa(16),wb(16);
      rcc_scope::Executor ca(cg,cr,rcc_scope::Kind::COUNT_ONLY),cb(cg,cr,rcc_scope::Kind::SCOPE_GLOBAL);
      for(U s=0;s<16;++s){auto a=ca.run<true>(s,wa),b=cb.run<true>(s,wb);check(wa.base.distance==wb.base.distance&&a.levels==b.levels&&b.edges<=a.edges&&b.vertex_tests<=a.vertex_tests,"matched-scope invariant");}}
    std::cout<<"{\"status\":\"PASS\",\"graphs\":"<<graph_count<<",\"mode_query_comparisons\":"<<comparisons<<",\"closure_edge_assertions\":"<<scope_assertions<<",\"assertions\":"<<assertions<<",\"gpu_runs\":0,\"sanitizer_runs\":0}\n";
}
static void diagnose(const std::string&dir,const std::string&out){std::ofstream csv(out+"/work.csv"),arrays(out+"/arrays.jsonl");
    csv<<"graph,schedule,mode,query_index,source,seen,domain,hit,edges,vertex_tests,levels,bitmap_clear,publish_tests,publish_writes,remaining_global,remaining_scope,stop_reason,extra_bytes\n";
    L requests=0,exports=0;
    for(auto&c:cases(dir)){auto g=Graph::load(dir+"/"+c.file,c.n,1);auto r=build(g);std::vector<std::vector<int>>want;for(U s:c.sources)want.push_back(reference(*g,s));
      for(auto&m:modes){Runner run(g,r,m);for(U i=0;i<c.sources.size();++i){auto a=run.run<true>(c.sources[i]);++requests;check(a.complete&&run.output()==want[i],"fixture mode mismatch");
          csv<<c.name<<','<<c.schedule<<','<<m<<','<<i<<','<<c.sources[i]<<','<<a.seen<<','<<a.domain_size<<','<<a.hit<<','<<a.edges<<','<<a.vertex_tests<<','<<a.levels<<','<<a.bitmap_clear<<','<<a.publish_tests<<','<<a.publish_writes<<','<<a.remaining_global<<','<<a.remaining_scope<<','<<a.stop_reason<<','<<run.extra()<<'\n';
          if(i==0||i==1||i==2||i==32){++exports;arrays<<"{\"graph\":\""<<c.name<<"\",\"file\":\""<<c.file<<"\",\"n\":"<<c.n<<",\"schedule\":\""<<c.schedule<<"\",\"mode\":\""<<m<<"\",\"source\":"<<c.sources[i]<<",\"distance\":";arr(arrays,run.output());arrays<<"}\n";}
      }}}
    std::cout<<"{\"status\":\"PASS\",\"fixture_requests\":"<<requests<<",\"exported_arrays\":"<<exports<<",\"checks\":"<<assertions<<"}\n";
}
static void bench(const std::string&dir,U session,bool cold){require(session<3,"at most 3 timing processes");volatile L sink=0;
    std::cout<<"graph,schedule,session,round,q,mode,elapsed_ns,extra_bytes,workspace_bytes,reused_result,boundary,checksum\n";
    for(auto&c:cases(dir)){auto g=Graph::load(dir+"/"+c.file,c.n,1);auto reverse=cold?std::shared_ptr<const Reverse>{}:build(g);std::vector<std::vector<int>>want;for(U s:c.sources)want.push_back(reference(*g,s));
      for(U q:(cold?std::vector<U>{32}:std::vector<U>{8,32})){std::vector<int>history(std::size_t(c.n)*(q+1));
        for(U round=0;round<(cold?3u:7u);++round)for(U turn=0;turn<modes.size();++turn){auto&m=modes[(turn+round+session)%modes.size()];L bytes=0,work_bytes=0,reuses=0;
            auto t0=Clock::now();{
              auto r=reverse;if(cold&&m.rfind("PUSH",0)!=0)r=build(g);
              Runner run(g,r,m);work_bytes=run.w.bytes();
              for(U i=0;i<=q;++i){auto a=run.run<false>(c.sources[i]);require(a.complete,"timed incomplete");std::copy(run.output().begin(),run.output().end(),history.begin()+L(i)*c.n);}
              bytes=run.extra();reuses=run.identical_source_reuses;
            }auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t0).count();
            for(U i=0;i<=q;++i)check(std::equal(want[i].begin(),want[i].end(),history.begin()+L(i)*c.n),"timed correctness mismatch");
            L sum=0;for(U i=0;i<=q;++i)sum+=U(history[L(i)*c.n+c.sources[i]])+i;sink+=sum;
            std::cout<<c.name<<','<<c.schedule<<','<<session<<','<<round<<','<<q<<','<<m<<','<<ns<<','<<bytes<<','<<work_bytes<<','<<reuses<<','<<(cold?"CPU_RESIDENT_CSR_COLD_REVERSE_AND_CERT":"CPU_RESIDENT_REVERSE_COLD_CERT")<<','<<sum<<'\n';
        }
      }
    }std::cerr<<"{\"status\":\"PASS\",\"checks\":"<<assertions<<",\"checksum\":"<<sink<<"}\n";
}
int main(int argc,char**argv){try{
    if(argc==2&&std::string(argv[1])=="test")tests();
    else if(argc==4&&std::string(argv[1])=="diagnose")diagnose(argv[2],argv[3]);
    else if(argc==4&&(std::string(argv[1])=="bench"||std::string(argv[1])=="cold"))bench(argv[2],U(std::stoul(argv[3])),std::string(argv[1])=="cold");
    else throw std::runtime_error("usage: scope_probe test | diagnose FIXTURES OUT | bench|cold FIXTURES SESSION0..2");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
