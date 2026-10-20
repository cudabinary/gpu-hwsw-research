#include "rcc/v1.hpp"
#ifndef DG_POLICY
#define DG_POLICY 9
#endif
#ifndef DG_DEFERRED
#define DG_DEFERRED 0
#endif
#ifndef DG_TIMERS
#define DG_TIMERS 0
#endif
namespace rcc_api {Module*make_experimental(unsigned,bool,bool);}
extern "C" rcc_api::Module*rcc_create(unsigned v){return v==rcc_api::API_VERSION?rcc_api::make_experimental(DG_POLICY,DG_DEFERRED,DG_TIMERS):nullptr;}
extern "C" void rcc_destroy(rcc_api::Module*p){delete p;}
