// CPU-only tests of the new preparation and the unchanged stop/replay contract.
int fair_tests(){
 require(native::dll==nullptr&&native::launched==0,"CPU tests reached driver");
 U graphs=0,arrays=0,bounds=0,negative=0;
 auto check_graph=[&](U n,const std::vector<std::pair<independent::U,independent::U>>&edges){
  auto g=std::make_shared<const independent::Graph>(n,901,edges);
  auto ap=std::make_shared<independent::Account>(32ULL<<20),ad=std::make_shared<independent::Account>(32ULL<<20);
  auto p=fair::prepare(g,7,ap),d=fair::prepare(g,5,ad);
  require(!p.reverse&&p.bound.payload_bytes()==8*((L(n)+63)/64)&&ap->live()==p.bound.payload_bytes(),"Push preparation allocation");
  require(d.reverse&&d.bound.payload_bytes()==0,"Direction preparation allocation");
  auto old=host_control::IncomingBound::prepare(*g,*d.reverse);
  for(U s=0;s<n;++s){
   auto exact=oracle(*g,s);auto push=replay(*g,nullptr,p.bound,s,7);auto direction=replay(*g,d.reverse.get(),d.bound,s,5);
   require(push.d==exact&&direction.d==exact,"full CPU distance");arrays+=2;
   require(p.bound.limit(*g,s)==old.limit(*g,*d.reverse,s),"CSR bitmap/reverse bound equivalence");++bounds;
  }++graphs;
 };
 for(U n=1;n<=3;++n)for(U mask=0;mask<(1u<<(n*n));++mask){
  std::vector<std::pair<independent::U,independent::U>>e;
  for(U a=0;a<n;++a)for(U b=0;b<n;++b)if(mask&(1u<<(a*n+b)))e.emplace_back(a,b);
  check_graph(n,e);
 }
 check_graph(3,{{0,1},{0,1},{1,2}});
 check_graph(5,{{0,1},{2,3},{3,2},{3,4},{4,4}});
 check_graph(4,{});
 check_graph(65,{{0,64},{64,1},{1,1},{64,1}});
 auto g=std::make_shared<const independent::Graph>(3,19,std::vector<std::pair<independent::U,independent::U>>{{0,1},{1,2}});
 auto account=std::make_shared<independent::Account>(1024);
 auto metadata=fair::CsrIncomingBound::prepare(g,account);
 auto other=std::make_shared<const independent::Graph>(*g);
 require(!metadata.can_apply(*other)&&metadata.limit(*other,0)==other->n(),"identity fallback");++negative;
 auto newer=std::make_shared<const independent::Graph>(3,20,std::vector<std::pair<independent::U,independent::U>>{{0,1},{1,2}});
 require(!metadata.can_apply(*newer)&&metadata.limit(*newer,0)==newer->n(),"version fallback");++negative;
 fair::CsrIncomingBound missing;require(missing.limit(*g,0)==g->n(),"missing metadata fallback");++negative;
 bool caught=false;try{metadata.limit(*g,3);}catch(const std::exception&){caught=true;}require(caught,"invalid source");++negative;
 auto fail=std::make_shared<independent::Account>(1024);fail->fail_after=0;caught=false;
 try{auto invalid=fair::CsrIncomingBound::prepare(g,fail);}catch(const std::bad_alloc&){caught=true;}
 require(caught&&fail->live()==0,"metadata allocation failure rollback");++negative;
 auto tiny=std::make_shared<independent::Account>(7);caught=false;
 try{auto invalid=fair::CsrIncomingBound::prepare(g,tiny);}catch(const std::bad_alloc&){caught=true;}
 require(caught&&tiny->live()==0,"metadata capacity rollback");++negative;
 std::atomic<bool>cancel{true};auto cancelled=std::make_shared<independent::Account>(1024);caught=false;
 try{auto invalid=fair::CsrIncomingBound::prepare(g,cancelled,&cancel);}catch(const std::exception&){caught=true;}
 require(caught&&cancelled->live()==0&&cancelled->calls==0,"metadata pre-cancel");++negative;
 caught=false;try{auto invalid=fair::prepare(g,5,cancelled,&cancel);}catch(const std::exception&){caught=true;}
 require(caught&&cancelled->live()==0,"Direction pre-cancel");++negative;
 std::weak_ptr<const independent::Graph>lifetime;
 {auto local=std::make_shared<const independent::Graph>(*g);lifetime=local;
  {auto own=fair::CsrIncomingBound::prepare(local,std::make_shared<independent::Account>(1024));local.reset();require(!lifetime.expired(),"metadata reader lifetime");}
  require(lifetime.expired(),"metadata releases lifetime");}++negative;
 require(!host_control::degree_stats(7)&&!host_control::direction(7),"Push null reverse safety predicates");++negative;
 require(sizeof(rgpu::View)==112&&sizeof(rgpu::Counter)==24,"unchanged kernel ABI");
 require(native::dll==nullptr&&native::launched==0,"CPU tests reached driver");
 std::cout<<"{\"status\":\"FAIR_HOST_CPU_TEST_PASS\",\"graphs\":"<<graphs<<",\"full_arrays\":"<<arrays<<",\"bound_equivalence_checks\":"<<bounds<<",\"negative_or_lifetime_checks\":"<<negative<<",\"driver_loaded\":false,\"GPU_launches\":0}\n";return 0;
}
