#pragma once
#include <cstddef>
namespace rgpu {
using U=unsigned int;using L=unsigned long long;
struct Counter{L found,out_edges,in_edges;};
struct View{
 U n,m;L graph_version,reverse_version,epoch;
 const L*row;const U*col;const L*rrow;const U*rsource;
 U*front;U*next;int*distance;L*bitmap;Counter*counter;U*error;
};
static_assert(sizeof(U)==4&&sizeof(L)==8&&sizeof(void*)==8);
static_assert(sizeof(Counter)==24);
static_assert(sizeof(View)==112);
}
