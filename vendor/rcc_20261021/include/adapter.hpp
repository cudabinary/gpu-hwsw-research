#pragma once
#include "stop_bridge.hpp"
#include <numeric>
#include <deque>
#include <chrono>
namespace merged {
using namespace independent;
using Cache=stop_bridge::Cache;
constexpr unsigned N=stop_bridge::N,RIE=stop_bridge::RIE,RCC=stop_bridge::RCC;
struct Mode {const char*name; bool push; unsigned flags; Cache cache; int legacy=0;bool wcc=false,reuse=false;};
inline const std::vector<Mode>&modes(){static const std::vector<Mode>v={
 {"OLD_P0",true,0,Cache::NONE,1},{"OLD_P2",false,0,Cache::NONE,2},
 {"PUSH_N",true,N,Cache::NONE},{"DO_N",false,N,Cache::NONE},{"DO_RIE",false,N|RIE,Cache::NONE},
 {"PUSH_RCC_LAST",true,N|RCC,Cache::LAST},{"PUSH_RCC_TABLE",true,N|RCC,Cache::TABLE},
 {"DO_RIE_RCC_LAST",false,N|RIE|RCC,Cache::LAST},{"DO_RIE_RCC_TABLE",false,N|RIE|RCC,Cache::TABLE},
 {"PUSH_TABLE_OFF",true,N,Cache::TABLE},{"DO_RIE_TABLE_OFF",false,N|RIE,Cache::TABLE},
 {"PUSH_LAST_OFF",true,N,Cache::LAST},{"DO_RIE_LAST_OFF",false,N|RIE,Cache::LAST},
 {"PUSH_WCC",true,N,Cache::NONE,0,true},{"LAST_RESULT_REUSE",true,N,Cache::LAST,0,false,true},
 {"DO_N_RCC_TABLE",false,N|RCC,Cache::TABLE},{"DO_N_TABLE_OFF",false,N,Cache::TABLE}};return v;}
inline Mode mode(const std::string&s){for(auto m:modes())if(s==m.name)return m;throw std::runtime_error("mode");}
struct Work:stop_bridge::Work{L expanded_rows=0,stop_checks=0,return_copy=0,allocations=0,reuse_hits=0;};
struct Output {
private:
 friend class Executor;
 std::shared_ptr<const Graph>g_;U source_,count_;std::vector<int>d_;
 Output(std::shared_ptr<const Graph>g,U s,U count,const std::vector<int>&d):g_(std::move(g)),source_(s),count_(count),d_(d){}
public:
 const std::vector<int>&distance()const{return d_;}
 U source()const{return source_;}U count()const{return count_;}
 const Graph*identity()const{return g_.get();}
};
using Result=std::shared_ptr<const Output>;
inline std::vector<int> oracle(const Graph&g,U s){
 std::vector<int>d(g.n(),-1);std::deque<U>q;q.push_back(s);d[s]=0;
 while(!q.empty()){U u=q.front();q.pop_front();for(L p=g.row()[u];p<g.row()[u+1];++p){U v=g.col()[p];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;
}
inline std::shared_ptr<const Reverse> build(std::shared_ptr<const Graph>g){
 auto a=std::make_shared<Account>(32ULL<<20);Builder b(g,a);b.finish();return b.take();
}
class Executor {
 std::shared_ptr<const Graph>g_;std::shared_ptr<const Reverse>r_;Mode m_;
 std::vector<U>table_,parent_,size_,wcc_;Result last_;
 U root(U x){while(parent_[x]!=x){parent_[x]=parent_[parent_[x]];x=parent_[x];}return x;}
 void publish(Result out,U before,Work&st,bool trace){
  if(m_.cache==Cache::LAST)last_=out;
  else if(m_.cache==Cache::TABLE&&out->count()<before){
   for(U v=0;v<g_->n();++v){if(trace)++st.publish_visits;
    if(out->distance()[v]>=0&&table_[v]>out->count()){table_[v]=out->count();if(trace)++st.publish_writes;}}
  }
 }
 Result complete(U s,U count,const std::vector<int>&d,U before,Work&st,bool trace,bool fail){
  if(fail)throw std::bad_alloc();
  Result out(new Output(g_,s,count,d));st.return_copy=g_->n();st.allocations=2;
  publish(out,before,st,trace);return out;
 }
public:
 bool fallback=false;
 Executor(std::shared_ptr<const Graph>g,std::shared_ptr<const Reverse>r,Mode m,L cache_limit=32ULL<<20,bool inject_cache_failure=false,bool deferred_reverse=false):g_(std::move(g)),r_(std::move(r)),m_(m){
  require(g_&&g_->n()>0&&g_->n()<=U(INT32_MAX),"graph size");
  if(!m_.push&&!deferred_reverse)require(r_&&r_->graph_ptr().get()==g_.get(),"reverse identity");
  L need=m_.wcc?12ULL*g_->n():m_.cache!=Cache::NONE?4ULL*g_->n():0;
  try{
   if(need>cache_limit||(need&&inject_cache_failure))throw std::bad_alloc();
   if(m_.cache==Cache::TABLE)table_.assign(g_->n(),g_->n());
   if(m_.wcc){
    parent_.resize(g_->n());std::iota(parent_.begin(),parent_.end(),0);size_.assign(g_->n(),1);
    for(U u=0;u<g_->n();++u)for(L e=g_->row()[u];e<g_->row()[u+1];++e){U a=root(u),b=root(g_->col()[e]);if(a!=b){if(size_[a]<size_[b])std::swap(a,b);parent_[b]=a;size_[a]+=size_[b];}}
    wcc_.resize(g_->n());for(U v=0;v<g_->n();++v)wcc_[v]=size_[root(v)];
   }
  }catch(const std::bad_alloc&){
   std::vector<U>().swap(table_);std::vector<U>().swap(parent_);std::vector<U>().swap(size_);std::vector<U>().swap(wcc_);
   m_=mode(m_.push?"PUSH_N":"DO_RIE");fallback=true;
  }
 }
 U bound(U s)const{
  require(s<g_->n(),"source");
  if(!wcc_.empty())return wcc_[s];
  if(m_.cache==Cache::TABLE)return table_[s];
  if(last_&&last_->distance()[s]>=0)return last_->count();
  return g_->n();
 }
 L cache_bytes()const{return 4ULL*(table_.capacity()+parent_.capacity()+size_.capacity()+wcc_.capacity());}
 bool retains_output()const{return bool(last_);}
 void bind_reverse(std::shared_ptr<const Reverse>r){require(r&&r->graph_ptr().get()==g_.get(),"reverse identity");r_=std::move(r);}
 void reset(){last_.reset();std::fill(table_.begin(),table_.end(),g_->n());}
 template<bool Trace=false>
 std::pair<Result,Work> run(U s,consumer::Workspace&w,L budget=std::numeric_limits<L>::max(),bool fail_output=false){
  require(w.base.distance.size()==g_->n()&&w.base.queue.size()==g_->n(),"workspace");
  U before=bound(s);Work st;st.limit=((m_.flags&RCC)||m_.wcc)?before:g_->n();
  if(m_.reuse&&last_&&last_->source()==s){st.seen=last_->count();st.complete=true;st.reuse_hits=1;return {last_,st};}
  if(m_.legacy){
   require(budget==std::numeric_limits<L>::max(),"legacy cancellation unsupported");
   auto cm=m_.legacy==1?consumer::Mode::QUEUE_PUSH:consumer::Mode::DIRECTION;
   if constexpr(Trace){
    auto d=consumer::diagnose(cm,*g_,*r_,s,w);for(auto l:d.levels){st.edges+=l.csr_edges+l.reverse_edges;st.vertex_tests+=l.unvisited_vertex_tests;st.bitmap_clear+=l.bitmap_words_cleared;st.bitmap_set+=l.bitmap_set_ops;}st.levels=d.levels.size();
   }else consumer::function(cm)(*g_,r_.get(),s,w);
   st.seen=0; // legacy has no certificate; count only in diagnostic path
   if constexpr(Trace)for(int d:w.base.distance)st.seen+=d>=0;
   st.complete=true;
  }else if(!m_.push){
   require(r_&&r_->graph_ptr().get()==g_.get(),"reverse not ready");
   static_cast<stop_bridge::Work&>(st)=stop_bridge::direction<Trace>(*g_,*r_,s,w,m_.flags,st.limit,budget);
   if constexpr(Trace)st.stop_checks=st.levels+1;
  }else{
   auto&d=w.base.distance;auto&q=w.base.queue;std::fill(d.begin(),d.end(),-1);d[s]=0;q[0]=s;
   U h=0,t=1;int lastlevel=-1;
   while(h<t&&t<st.limit){
    if(h>=budget){st.seen=t;return {nullptr,st};}
    U u=q[h++];if constexpr(Trace){++st.expanded_rows;++st.stop_checks;if(d[u]!=lastlevel){++st.levels;lastlevel=d[u];}}
    for(L p=g_->row()[u];p<g_->row()[u+1];++p){if constexpr(Trace)++st.edges;U v=g_->col()[p];if(d[v]<0){d[v]=d[u]+1;q[t++]=v;}}
   }
   require(t<=st.limit,"invalid upper bound");st.seen=t;st.complete=true;
   st.reason=h<t?(st.limit==g_->n()?1:3):0;
  }
  if(!st.complete)return {nullptr,st};
  return {complete(s,st.seen,w.base.distance,before,st,Trace,fail_output),st};
 }
 // A stays the frozen, unmodified queue BFS. Counting a completed output is
 // certificate publication work and is included in A completion by the caller.
 std::pair<Result,Work> run_a(U s,consumer::Workspace&w,double&compute_ns){
  U before=bound(s);auto start=std::chrono::steady_clock::now();plan_a(*g_,s,w.base);
  compute_ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
  U count=0;if(m_.cache!=Cache::NONE)for(int d:w.base.distance)count+=d>=0;
  Work st;st.complete=true;st.seen=count;
  return {complete(s,count,w.base.distance,before,st,false,false),st};
 }
};
}
