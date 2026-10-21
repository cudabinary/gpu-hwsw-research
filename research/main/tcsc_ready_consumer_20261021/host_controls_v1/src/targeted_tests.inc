// Targeted CPU checks of the actual shared stop helper and generated replay.
struct SmallCase{const char*name;U n,source;std::vector<std::pair<independent::U,independent::U>>edges;};
std::vector<int> unsafe_bound_bfs(U n,const std::vector<std::pair<independent::U,independent::U>>&edges,
                                const std::vector<U>&seeds,U bound,bool count_attempts=false){
 std::vector<std::vector<U>>adj(n);for(auto e:edges)adj[e.first].push_back(e.second);
 std::vector<int>d(n,-1);std::vector<U>front=seeds;for(U s:seeds)d[s]=0;U seen=U(seeds.size());
 while(!front.empty()){
  if(seen==bound)break;
  std::vector<U>next;
  for(U u:front)for(U v:adj[u]){
   if(count_attempts)++seen;
   if(d[v]<0){d[v]=d[u]+1;next.push_back(v);if(!count_attempts)++seen;}
  }front.swap(next);
 }return d;
}
struct FakeGraph{U vertices;L edges,version_tag;U n()const{return vertices;}L m()const{return edges;}L version()const{return version_tag;}};
struct FakeReverse{
 std::shared_ptr<FakeGraph>g;std::vector<L>offset;
 const auto&graph_ptr()const{return g;}const auto&graph()const{return *g;}const L*row()const{return offset.data();}
};
int control_tests(){
 require(native::dll==nullptr,"CPU tests driver loaded");
 const std::vector<SmallCase>cases={
  {"zero_indegree_source",3,0,{{0,1},{1,2}}},
  {"positive_indegree_source",3,1,{{0,1},{1,2}}},
  {"duplicates",3,0,{{0,1},{0,1},{1,2}}},
  {"unreachable_positive_scc",5,0,{{0,1},{2,3},{3,2},{3,4},{4,4}}},
  {"edgeless",4,2,{}},
  {"isolated_zero_indegree_vertices",5,1,{{1,2},{2,3}}},
  {"self_loop",1,0,{{0,0}}},
  {"directed_sink_source",3,2,{{0,1},{1,2}}}};
 U arrays=0,equal_stops=0,negative=0,identities=0;
 for(const auto&t:cases){
  auto g=std::make_shared<const independent::Graph>(t.n,17,t.edges);
  auto account=std::make_shared<independent::Account>(1ULL<<20);independent::Builder b(g,account);b.finish();auto r=b.take();
  auto expected=oracle(*g,t.source);auto bound=host_control::IncomingBound::prepare(*g,*r);
  for(U mode:{0u,5u,7u,8u}){auto a=replay(*g,*r,t.source,mode);require(a.d==expected,"targeted full distance mismatch");++arrays;}
  auto direction=replay(*g,*r,t.source,5),push=replay(*g,*r,t.source,8);
  require(direction.levels==push.levels&&direction.seen==push.seen,"equal stop boundary mismatch");++equal_stops;
  U seen=0;L remaining=g->m();
  int depth=*std::max_element(expected.begin(),expected.end());
  for(int level=0;level<=depth;++level){
   for(U v=0;v<t.n;++v)if(expected[v]==level){++seen;remaining-=r->row()[v+1]-r->row()[v];}
   require((remaining==0)==(seen==bound.limit(*g,*r,t.source)),"RIE/static identity");++identities;
  }
  std::cout<<"{\"kind\":\"TARGETED_GRAPH\",\"name\":\""<<t.name<<"\",\"arrays\":4,\"positive_indegree\":"<<bound.positive_vertices()<<",\"source_bound\":"<<bound.limit(*g,*r,t.source)<<"}\n";
 }
 const std::vector<std::pair<independent::U,independent::U>>path{{0,1},{1,2}},duplicate{{0,1},{0,1},{1,2}};
 auto exact=std::vector<int>{0,1,2};
 require(unsafe_bound_bfs(3,path,{0},2)!=exact,"missing source exception witness");++negative;
 require(unsafe_bound_bfs(3,duplicate,{0},3,true)!=exact,"nonunique seen witness");++negative;
 require(unsafe_bound_bfs(3,path,{0},2)!=exact,"stale scalar witness");++negative;
 require(unsafe_bound_bfs(4,{{0,2},{2,3}},{0,1},3)!=std::vector<int>({0,0,1,2}),"multisource witness");++negative;
 auto fg=std::make_shared<FakeGraph>(FakeGraph{3,2,1});FakeReverse fr{fg,{0,0,1,2}};
 auto metadata=host_control::IncomingBound::prepare(*fg,fr);require(metadata.limit(*fg,fr,0)==3,"prepared bound");
 host_control::IncomingBound unavailable;require(unavailable.limit(*fg,fr,0)==3,"missing metadata EARLY_N fallback");++negative;
 auto other=std::make_shared<FakeGraph>(*fg);FakeReverse other_r{other,fr.offset};
 require(!metadata.can_apply(*other,other_r)&&metadata.limit(*other,other_r,0)==3,"identity fallback");++negative;
 FakeReverse second_r{fg,fr.offset};require(!metadata.can_apply(*fg,second_r)&&metadata.limit(*fg,second_r,0)==3,"reverse identity fallback");++negative;
 fg->version_tag=2;require(!metadata.can_apply(*fg,fr)&&metadata.limit(*fg,fr,0)==3,"version fallback");++negative;
 bool caught=false;try{metadata.limit(*fg,fr,3);}catch(const std::invalid_argument&){caught=true;}require(caught,"invalid source reject");++negative;
 FakeReverse wrong_shape{fg,{0,0,1,1}};caught=false;try{host_control::IncomingBound::prepare(*fg,wrong_shape);}catch(const std::invalid_argument&){caught=true;}require(caught,"partial count reject");++negative;
 // A forged complete-size histogram can pass shape checks. Exact reverse
 // semantics and immutability are prerequisites, not inferred from its size.
 FakeReverse forged{fg,{0,0,2,2}};auto forged_bound=host_control::IncomingBound::prepare(*fg,forged);
 require(unsafe_bound_bfs(3,path,{0},forged_bound.limit(*fg,forged,0))!=exact,"forged degrees witness");++negative;
 require(host_control::stop(8,1,4,0,0,1)==4,"zero precedes bound");++negative;
 require(host_control::stop(8,4,4,0,0,4)==1,"EARLY_N precedes zero");++negative;
 require(!host_control::supported(1)&&!host_control::supported(2)&&!host_control::supported(3),"unplanned modes excluded");++negative;
 require(native::dll==nullptr&&native::launched==0,"CPU test reached driver");
 std::cout<<"{\"kind\":\"SUMMARY\",\"status\":\"CPU_TARGETED_PASS\",\"full_arrays\":"<<arrays<<",\"equal_stop_checks\":"<<equal_stops<<",\"identity_boundaries\":"<<identities<<",\"negative_or_boundary_checks\":"<<negative<<",\"metadata_bytes\":"<<sizeof(host_control::IncomingBound)<<",\"driver_loaded\":false,\"GPU_launches\":0}\n";
 return 0;
}
