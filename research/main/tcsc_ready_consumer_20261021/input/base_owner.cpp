// Native Windows owner, not an empty-main static stub.
// No CUDA API is reached by --abi or --cpu-check.
#include "native_driver.hpp"
#include "abi.hpp"
#include "independent_builder.hpp"
#include <chrono>
#include <deque>
#include <iostream>
#include <sstream>
#include <iomanip>
using rgpu::U;using rgpu::L;using rgpu::View;using rgpu::Counter;
using independent::require;
using Clock=std::chrono::steady_clock;
double milliseconds(Clock::time_point t){return std::chrono::duration<double,std::milli>(Clock::now()-t).count();}
void ck(CUresult r){native::check(r);}
void reserve(size_t need=0){size_t free=0,total=0;ck(cudaMemGetInfo(&free,&total));require(free>=1536ULL*1024*1024&&need<=free-1536ULL*1024*1024,"1536 MiB free reserve");}
std::vector<int> oracle(const independent::Graph&g,U s){
 std::vector<int>d(g.n(),-1);std::deque<U>q;q.push_back(s);d[s]=0;
 while(!q.empty()){U u=q.front();q.pop_front();for(auto e=g.row()[u];e<g.row()[u+1];++e){U v=g.col()[e];if(d[v]<0){d[v]=d[u]+1;q.push_back(v);}}}return d;
}
struct Arena{
 std::vector<void*>p;size_t bytes=0;
 template<class T>T*alloc(size_t count){size_t b=std::max<size_t>(1,count)*sizeof(T);require(b<=(32ULL<<20)-bytes,"32 MiB owned cap");reserve(b);void*x{};ck(cudaMalloc(&x,b));p.push_back(x);bytes+=b;return static_cast<T*>(x);}
 void close(){for(void*x:p)ck(cudaFree(x));p.clear();}
 ~Arena(){for(void*x:p)cudaFree(x);}
};
class Owner{
 std::shared_ptr<const independent::Graph>g_;
 std::shared_ptr<const independent::Reverse>r_;
 std::vector<U>table_;
 Arena arena_;cudaStream_t stream_{};View d_{};U mode_;L epoch_=0;
 bool failed_=false;
public:
 Owner(std::shared_ptr<const independent::Graph>g,std::shared_ptr<const independent::Reverse>r,U mode):g_(std::move(g)),r_(std::move(r)),mode_(mode){
  require(mode<=3&&g_->n()<=4096&&g_->m()<=131072,"pilot bounds");
  require(mode<2||(r_&&r_->graph_ptr().get()==g_.get()),"reverse identity");
  ck(cudaStreamCreateWithPriority(&stream_,cudaStreamNonBlocking,0));
  d_.n=g_->n();d_.m=U(g_->m());d_.graph_version=g_->version();d_.reverse_version=r_?r_->graph().version():0;
  auto row=arena_.alloc<L>(d_.n+1);auto col=arena_.alloc<U>(d_.m);d_.row=row;d_.col=col;
  ck(cudaMemcpy(row,g_->row().data(),8ULL*(d_.n+1),cudaMemcpyHostToDevice));
  if(d_.m)ck(cudaMemcpy(col,g_->col().data(),4ULL*d_.m,cudaMemcpyHostToDevice));
  d_.front=arena_.alloc<U>(d_.n);d_.next=arena_.alloc<U>(d_.n);d_.distance=arena_.alloc<int>(d_.n);d_.counter=arena_.alloc<Counter>(1);d_.error=arena_.alloc<U>(1);
  if(mode>=2){
   auto row=arena_.alloc<L>(d_.n+1);auto src=arena_.alloc<U>(d_.m);d_.rrow=row;d_.rsource=src;d_.bitmap=arena_.alloc<L>((d_.n+63)/64);
   ck(cudaMemcpy(row,r_->row(),8ULL*(d_.n+1),cudaMemcpyHostToDevice));if(d_.m)ck(cudaMemcpy(src,r_->source(),4ULL*d_.m,cudaMemcpyHostToDevice));
  }
  if(mode==1)table_.assign(d_.n,d_.n);
  ck(cudaStreamSynchronize(stream_));reserve();
 }
 struct Answer{
  bool complete=false;std::shared_ptr<const std::vector<int>>distance;
  U seen=0,levels=0,bound=0,reason=0,kernels=0;L remaining=0;double wall_ms=0,stream_interval_ms=0,copy_ms=0,publish_ms=0;
 };
 Answer query(U source,U maxlevels=128){
  require(!failed_&&source<d_.n&&epoch_<~L(0),"owner/source/epoch");
  require(!r_||(r_->graph_ptr().get()==g_.get()&&r_->graph().version()==d_.graph_version),"reader identity");
  Answer a;auto start=Clock::now();unsigned before=native::launched;cudaEvent_t begin{},end{};
  try{
   ++epoch_;d_.epoch=epoch_;a.bound=mode_==1?table_[source]:d_.n;a.seen=1;
   L remaining=mode_>=2?d_.m-(r_->row()[source+1]-r_->row()[source]):0;
   L fe=g_->row()[source+1]-g_->row()[source];U count=1;bool pull=false;
   ck(cudaEventCreateWithFlags(&begin,0));ck(cudaEventCreateWithFlags(&end,0));ck(cudaEventRecord(begin,stream_));
   native::launch("r_init",(d_.n+127)/128,128,stream_,d_,source);
   // An explicit cancellation consumes initialization but publishes no output.
   if(!maxlevels){ck(cudaStreamSynchronize(stream_));ck(cudaEventDestroy(begin));ck(cudaEventDestroy(end));a.kernels=native::launched-before;a.wall_ms=milliseconds(start);return a;}
   while(count){
    require(native::launched<2040,"bounded kernel dispatch");
    require(a.seen<=a.bound,"invalid RCC bound");
    if(a.seen==d_.n){a.reason=1;break;}
    if(mode_==3&&remaining==0){a.reason=2;break;}
    if(mode_==1&&a.seen==a.bound){a.reason=3;break;}
    require(a.levels<maxlevels,"level cap; no certificate published");
    ck(cudaMemsetAsync(d_.counter,0,sizeof(Counter),stream_));
    if(mode_>=2){
     if(pull){if(count<std::max<U>(1,d_.n/24))pull=false;}else if(fe>remaining/15)pull=true;
    }
    if(pull){
     ck(cudaMemsetAsync(d_.bitmap,0,8ULL*((d_.n+63)/64),stream_));
     native::launch("r_mark",(count+127)/128,128,stream_,d_,count);
     native::launch("r_pull",(d_.n+127)/128,128,stream_,d_,a.levels);
    }else native::launch("r_push",(count+127)/128,128,stream_,d_,count,a.levels,U(mode_>=2));
    ck(cudaStreamSynchronize(stream_));
    Counter c{};U error=0;ck(cudaMemcpy(&c,d_.counter,sizeof(c),cudaMemcpyDeviceToHost));ck(cudaMemcpy(&error,d_.error,4,cudaMemcpyDeviceToHost));
    require(!error&&c.found<=d_.n-a.seen,"device error/counter");
    if(mode_>=2){require(c.in_edges<=remaining,"remaining underflow");remaining-=c.in_edges;fe=c.out_edges;}
    a.seen+=U(c.found);count=U(c.found);std::swap(d_.front,d_.next);++a.levels;reserve();
   }
   ck(cudaEventRecord(end,stream_));ck(cudaEventSynchronize(end));
   float interval=0;ck(cudaEventElapsedTime(&interval,begin,end));a.stream_interval_ms=interval;
   ck(cudaEventDestroy(begin));begin=nullptr;ck(cudaEventDestroy(end));end=nullptr;
   auto copy=Clock::now();auto out=std::make_shared<std::vector<int>>(d_.n);ck(cudaMemcpy(out->data(),d_.distance,4ULL*d_.n,cudaMemcpyDeviceToHost));a.copy_ms=milliseconds(copy);
   auto pub=Clock::now();if(mode_==1&&a.seen<a.bound)for(U v=0;v<d_.n;++v)if((*out)[v]>=0)table_[v]=std::min(table_[v],a.seen);
   a.publish_ms=milliseconds(pub);a.distance=out;a.complete=true;a.remaining=remaining;a.kernels=native::launched-before;a.wall_ms=milliseconds(start);return a;
  }catch(...){failed_=true;if(begin)cudaEventDestroy(begin);if(end)cudaEventDestroy(end);throw;}
 }
 U bound(U s)const{return mode_==1?table_.at(s):d_.n;}
 size_t bytes()const{return arena_.bytes;}
 void close(){ck(cudaStreamSynchronize(stream_));arena_.close();ck(cudaStreamDestroy(stream_));stream_=nullptr;}
 ~Owner(){if(stream_)cudaStreamDestroy(stream_);}
};
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--abi"){std::cout<<"{\"View\":"<<sizeof(View)<<",\"Counter\":"<<sizeof(Counter)<<",\"row\":"<<offsetof(View,row)<<",\"counter\":"<<offsetof(View,counter)<<"}\n";return 0;}
 require(argc==8,"--cpu-check|--execute fixture n mode s0 s1 s2");
 std::string action=argv[1];require(action=="--cpu-check"||action=="--execute","action");
 U n=std::stoul(argv[3]),mode=std::stoul(argv[4]);require(n&&n<=4096&&mode<=3,"args");
 std::vector<U>sources={U(std::stoul(argv[5])),U(std::stoul(argv[6])),U(std::stoul(argv[7]))};
 for(U s:sources)require(s<n,"source range");
 auto g=independent::Graph::load(argv[2],n,20261021);require(g->m()<=131072,"edge cap");
 std::vector<std::vector<int>>expected;for(U s:sources)expected.push_back(oracle(*g,s));
 std::shared_ptr<const independent::Reverse>r;double build_ms=0;
 if(mode>=2){auto t=Clock::now();auto account=std::make_shared<independent::Account>(32ULL<<20);independent::Builder b(g,account);b.finish();r=b.take();build_ms=milliseconds(t);}
 if(action=="--cpu-check"){std::cout<<"CPU_ONLY_PASS no_driver_loaded="<<(native::dll==nullptr)<<"\n";return 0;}
 auto setup=Clock::now();native::init();
 const char*ack=std::getenv("TCSC_ACK");std::ifstream ackfile(ack?ack:"");unsigned ackpid=0;ackfile>>ackpid;require(ackpid==GetCurrentProcessId(),"ACK PID mismatch");
 char gpu_name[256]{};ck(DRV(cuDeviceGetName,gpu_name,256,native::device));require(std::string(gpu_name).find("4060 Ti")!=std::string::npos,"RTX 4060 Ti required");
 {Owner owner(g,r,mode);double setup_ms=milliseconds(setup);std::vector<std::shared_ptr<const std::vector<int>>>history;
 for(U i=0;i<3;++i){
  if(i==1){U old=owner.bound(sources[i]);auto aborted=owner.query(sources[i],0);require(!aborted.complete&&!aborted.distance&&owner.bound(sources[i])==old,"cancel changed certificate");
   std::cout<<"{\"kind\":\"cancel\",\"complete\":false,\"kernel_launches\":"<<aborted.kernels<<"}\n";}
  auto a=owner.query(sources[i]);auto v=Clock::now();require(a.complete&&a.distance&&*a.distance==expected[i],"GPU full distance correctness");double validation=milliseconds(v);history.push_back(a.distance);
  for(U j=0;j<=i;++j)require(*history[j]==expected[j],"retained reader corruption");
  std::cout<<std::setprecision(12)<<"{\"kind\":\"BFS\",\"status\":\"PASS\",\"mode\":"<<mode<<",\"source\":"<<sources[i]<<",\"query\":"<<i<<",\"seen\":"<<a.seen<<",\"bound\":"<<a.bound<<",\"levels\":"<<a.levels<<",\"reason\":"<<a.reason<<",\"remaining_in\":"<<a.remaining<<",\"kernel_launches\":"<<a.kernels<<",\"wall_ms\":"<<a.wall_ms<<",\"stream_interval_ms\":"<<a.stream_interval_ms<<",\"return_copy_ms\":"<<a.copy_ms<<",\"publication_ms\":"<<a.publish_ms<<",\"validation_ms\":"<<validation<<",\"device_payload_bytes\":"<<owner.bytes()<<",\"context_setup_transfer_ms\":"<<setup_ms<<",\"cpu_reverse_build_ms\":"<<build_ms<<"}\n"<<std::flush;
 }owner.close();}
 native::shutdown();std::cerr<<"CONTEXT_RELEASED_SYNC_OK kernels="<<native::launched<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<"STOP_NO_RETRY "<<e.what()<<"\n";return 2;}}
