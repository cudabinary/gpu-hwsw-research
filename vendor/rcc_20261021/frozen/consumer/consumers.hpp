#pragma once
#include "independent_builder.hpp"
namespace consumer {
using namespace independent;
constexpr U ALPHA=15,BETA=24;
enum class Mode:U {QUEUE_PUSH=0,PURE_PULL=1,DIRECTION=2,STATS_PUSH=3};
inline const char*name(Mode m){switch(m){case Mode::QUEUE_PUSH:return "P0_QUEUE_PUSH";case Mode::PURE_PULL:return "P1_PURE_PULL";case Mode::DIRECTION:return "P2_DIRECTION";case Mode::STATS_PUSH:return "P3_STATS_PUSH";}return "INVALID";}
struct Workspace {
    BfsWorkspace base;std::vector<U> next;std::vector<L> bitmap;
    explicit Workspace(U n,bool policy=true):base(n),next(policy?n:0),bitmap(policy?(L(n)+63)/64:0){}
    L bytes()const{return base.bytes()+4*L(next.capacity())+8*L(bitmap.capacity());}
};
struct Level {
    U level=0;L frontier=0,frontier_edges=0,remaining_in=0,discovered=0;
    bool shadow_pull=false,actual_pull=false;
    L csr_edges=0,reverse_edges=0,unvisited_vertex_tests=0,neighbor_distance_tests=0,bitmap_membership_tests=0;
    L queue_reads=0,queue_writes=0,bitmap_words_cleared=0,bitmap_set_ops=0,policy_vertex_updates=0,policy_offset_reads=0;
};
struct Diagnostic {std::vector<Level>levels;L initialized_distance_vertices=0;};
using Fn=void(*)(const Graph&,const Reverse*,U,Workspace&);
Fn function(Mode mode);
Diagnostic diagnose(Mode mode,const Graph&graph,const Reverse&reverse,U source,Workspace&workspace);
} // namespace consumer
