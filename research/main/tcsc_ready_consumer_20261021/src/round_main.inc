// Six predeclared consumers. Mode 1 (RCC) is deliberately excluded.
struct Replay { std::vector<int>d;U seen=1,levels=0,reason=0;L edges=0,rows=0,candidates=0; };
Replay replay(const independent::Graph&g,const independent::Reverse&r,U source,U mode){
 Replay a;a.d.assign(g.n(),-1);a.d[source]=0;std::vector<U>front{source};
 L remaining=g.m()-(r.row()[source+1]-r.row()[source]);
 L fe=g.row()[source+1]-g.row()[source];bool pull=false;
 while(!front.empty()){
  if(a.seen==g.n()){a.reason=1;break;}
  if((mode==4||mode==5)&&fe==0){a.reason=4;break;}
  if((mode==3||mode==5)&&remaining==0){a.reason=2;break;}
  if(mode>=2&&mode!=6){if(pull){if(front.size()<std::max<U>(1,g.n()/24))pull=false;}else if(fe>remaining/15)pull=true;}
  std::vector<U>next;L next_out=0,next_in=0;
  auto discover=[&](U v){a.d[v]=int(a.levels)+1;next.push_back(v);if(mode>=2){next_out+=g.row()[v+1]-g.row()[v];next_in+=r.row()[v+1]-r.row()[v];}};
  if(!pull){for(U u:front){++a.rows;for(L e=g.row()[u];e<g.row()[u+1];++e){++a.edges;U v=g.col()[e];if(a.d[v]<0)discover(v);}}}
  else {std::vector<unsigned char>bits(g.n(),0);for(U u:front)bits[u]=1;for(U v=0;v<g.n();++v)if(a.d[v]<0){++a.candidates;for(L e=r.row()[v];e<r.row()[v+1];++e){++a.edges;if(bits[r.source()[e]]){discover(v);break;}}}}
  if(mode>=2){require(next_in<=remaining,"CPU remaining underflow");remaining-=next_in;fe=next_out;}
  a.seen+=U(next.size());front.swap(next);++a.levels;
 }return a;
}
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--abi"){std::cout<<"{\"View\":"<<sizeof(View)<<",\"Counter\":"<<sizeof(Counter)<<",\"row\":"<<offsetof(View,row)<<",\"counter\":"<<offsetof(View,counter)<<"}\n";return 0;}
 require(argc==6,"--cpu-check|--execute fixture n mode q");
 std::string action=argv[1];require(action=="--cpu-check"||action=="--execute","action");
 U n=std::stoul(argv[3]),mode=std::stoul(argv[4]),q=std::stoul(argv[5]);
 require(n&&n<=4096&&(mode==0||(mode>=2&&mode<=6))&&(q==3||q==32),"fixed experiment args");
 std::vector<U>sources;if(q==3)sources={0,1,4};else for(U i=0;i<32;++i)sources.push_back(17*i);
 for(U source:sources)require(source<n,"source range");
 auto load_start=Clock::now();auto g=independent::Graph::load(argv[2],n,n==4096?1002:n==1024?1001:7001);
 require(g->m()<=131072,"edge cap");double load_ms=milliseconds(load_start);
 auto build_start=Clock::now();auto account=std::make_shared<independent::Account>(32ULL<<20);independent::Builder builder(g,account);builder.finish();auto reverse=builder.take();double build_ms=milliseconds(build_start);
 auto reference_start=Clock::now();std::vector<std::vector<int>>expected;std::vector<Replay>work;
 for(U source:sources){expected.push_back(oracle(*g,source));work.push_back(replay(*g,*reverse,source,mode));require(work.back().d==expected.back(),"CPU replay exact distance");}
 double reference_ms=milliseconds(reference_start);
 if(action=="--cpu-check"){require(native::dll==nullptr,"CPU path loaded driver");std::cout<<"{\"status\":\"CPU_ONLY_PASS\",\"arrays\":"<<q<<",\"mode\":"<<mode<<",\"no_driver_loaded\":true}\n";return 0;}
 auto setup_start=Clock::now();native::init();
 const char*ack=std::getenv("TCSC_ACK");std::ifstream ackfile(ack?ack:"");unsigned ackpid=0;ackfile>>ackpid;require(ackpid==GetCurrentProcessId(),"ACK PID mismatch");
 char name[256]{};ck(DRV(cuDeviceGetName,name,256,native::device));require(std::string(name).find("4060 Ti")!=std::string::npos,"RTX 4060 Ti required");
 {Owner owner(g,reverse,mode);double setup_ms=milliseconds(setup_start);std::vector<Owner::Answer>answers;std::vector<double>prefix;answers.reserve(q);prefix.reserve(q);
 auto batch_start=Clock::now();for(U source:sources){auto a=owner.query(source);require(a.complete&&a.distance,"missing owned output");prefix.push_back(milliseconds(batch_start));answers.push_back(std::move(a));}
 double batch_ms=milliseconds(batch_start);
 unsigned cancels=0;if(q==3){auto aborted=owner.query(sources[1],0);require(!aborted.complete&&!aborted.distance,"cancel publication");cancels=1;}
 auto validation_start=Clock::now();for(U i=0;i<q;++i){const auto&a=answers[i];require(*a.distance==expected[i],"GPU full distance mismatch");require(a.seen==work[i].seen&&a.levels==work[i].levels&&a.reason==work[i].reason,"GPU/replay trajectory mismatch");}
 double validation_ms=milliseconds(validation_start);
 const char* output_path=std::getenv("TCSC_DISTANCE_OUT");require(output_path,"owned output capture path");
 {std::ofstream output(output_path,std::ios::binary|std::ios::trunc);require(bool(output),"output capture open");for(const auto&a:answers)output.write(reinterpret_cast<const char*>(a.distance->data()),4ULL*g->n());require(bool(output),"output capture write");}
 for(U i=0;i<q;++i){const auto&a=answers[i];std::cout<<std::setprecision(12)<<"{\"kind\":\"BFS\",\"status\":\"PASS\",\"mode\":"<<mode<<",\"source\":"<<sources[i]<<",\"query\":"<<i<<",\"seen\":"<<a.seen<<",\"levels\":"<<a.levels<<",\"reason\":"<<a.reason<<",\"remaining_in\":"<<a.remaining<<",\"kernel_launches\":"<<a.kernels<<",\"wall_ms\":"<<a.wall_ms<<",\"stream_interval_ms\":"<<a.stream_interval_ms<<",\"return_copy_ms\":"<<a.copy_ms<<",\"owned_ready_prefix_ms\":"<<prefix[i]<<",\"reconstructed_edge_tests\":"<<work[i].edges<<",\"reconstructed_push_rows\":"<<work[i].rows<<",\"reconstructed_pull_candidates\":"<<work[i].candidates<<"}\n";}
 std::cout<<std::setprecision(12)<<"{\"kind\":\"BATCH\",\"status\":\"PASS\",\"q\":"<<q<<",\"mode\":"<<mode<<",\"batch_ms\":"<<batch_ms<<",\"device_payload_bytes\":"<<owner.bytes()<<",\"context_setup_transfer_ms\":"<<setup_ms<<",\"cpu_reverse_build_ms\":"<<build_ms<<",\"graph_load_ms\":"<<load_ms<<",\"cpu_reference_and_work_replay_ms\":"<<reference_ms<<",\"post_batch_validation_ms\":"<<validation_ms<<",\"cancel_tests\":"<<cancels<<",\"work_count_kind\":\"CODE_RECONSTRUCTION_NOT_GPU_MEMORY_TRAFFIC\"}\n"<<std::flush;
 owner.close();}native::shutdown();std::cerr<<"CONTEXT_RELEASED_SYNC_OK kernels="<<native::launched<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<"STOP_NO_RETRY "<<e.what()<<"\n";return 2;}}
