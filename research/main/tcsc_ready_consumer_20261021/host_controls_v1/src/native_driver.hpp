#pragma once
#define NOMINMAX
#include <windows.h>
#include <cuda.h>
#include <fstream>
#include <map>
#include <string>
#include <vector>
#include <stdexcept>
#include <cstdlib>
// Driver API adapter: no DLL, context or CUDA call before explicit init().
namespace native {
inline HMODULE dll=nullptr;inline CUmodule module{};inline CUdevice device{};
inline CUcontext context{};inline bool closed=false;inline unsigned launched=0;
template<class T>T load(const char* name){if(!dll)throw std::runtime_error("driver not initialized");auto p=GetProcAddress(dll,name);if(!p)throw std::runtime_error(std::string("missing CUDA API ")+name);return reinterpret_cast<T>(p);}
inline void check(CUresult e){if(e!=CUDA_SUCCESS){const char* text=nullptr;if(dll){auto f=load<decltype(&cuGetErrorString)>("cuGetErrorString");f(e,&text);}throw std::runtime_error(std::string("CUDA error ")+std::to_string(int(e))+": "+(text?text:"unavailable"));}}
#define DRV(fn,...) ([&](){static auto tcsc_api=native::load<decltype(&fn)>(#fn);return tcsc_api(__VA_ARGS__);}())
// Use explicit exported version strings for APIs that cuda.h aliases.
#define DRVV(fn,symbol,...) ([&](){static auto tcsc_api=native::load<decltype(&fn)>(symbol);return tcsc_api(__VA_ARGS__);}())
inline void init(){
 if(dll)return;
 if(!std::getenv("TCSC_GPU_APPROVED_TOKEN")||std::string(std::getenv("TCSC_GPU_APPROVED_TOKEN"))!="HUMAN_APPROVED_FINITE_PLAN")throw std::runtime_error("approval gate before DLL");
 dll=LoadLibraryExW(L"nvcuda.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!dll)throw std::runtime_error("nvcuda.dll unavailable");
 check(DRV(cuInit,0));int count=0;check(DRV(cuDeviceGetCount,&count));if(count!=1)throw std::runtime_error("one GPU required");check(DRV(cuDeviceGet,&device,0));
 check(DRV(cuDevicePrimaryCtxRetain,&context,device));check(DRV(cuCtxSetCurrent,context));
 const char* path=std::getenv("TCSC_CUBIN");if(!path)throw std::runtime_error("module path gate");
 std::ifstream in(path,std::ios::binary);std::vector<char> image((std::istreambuf_iterator<char>(in)),{});if(image.empty())throw std::runtime_error("module input missing");
 check(DRV(cuModuleLoadData,&module,image.data()));
 // A ready file does not authorize launches. Parent must acknowledge native PID.
 const char* ready=std::getenv("TCSC_READY"),*ack=std::getenv("TCSC_ACK");if(!ready||!ack)throw std::runtime_error("handshake gate missing");
 {std::ofstream o(ready);o<<GetCurrentProcessId()<<'\n';}
 auto start=GetTickCount64();while(GetFileAttributesA(ack)==INVALID_FILE_ATTRIBUTES){if(GetTickCount64()-start>4000)throw std::runtime_error("parent ACK timeout; no kernels");Sleep(10);}
}
inline void shutdown(){if(!dll||closed)return;check(DRV(cuCtxSynchronize));check(DRV(cuModuleUnload,module));check(DRVV(cuDevicePrimaryCtxRelease,"cuDevicePrimaryCtxRelease_v2",device));closed=true;}
template<class... Args>void launch(const char* name,unsigned grid,unsigned block,CUstream stream,Args... args){
 static std::map<std::string,CUfunction> functions;auto it=functions.find(name);if(it==functions.end()){CUfunction f{};check(DRV(cuModuleGetFunction,&f,module,name));it=functions.emplace(name,f).first;}
 void* params[]={static_cast<void*>(&args)...};check(DRV(cuLaunchKernel,it->second,grid,1,1,block,1,1,0,stream,params,nullptr));++launched;
}
}
using cudaError_t=CUresult;using cudaStream_t=CUstream;using cudaEvent_t=CUevent;
constexpr auto cudaSuccess=CUDA_SUCCESS,cudaErrorNotReady=CUDA_ERROR_NOT_READY;
constexpr unsigned cudaStreamNonBlocking=1,cudaEventDefault=0,cudaEventDisableTiming=2,cudaHostAllocDefault=0;
enum CopyKind{cudaMemcpyHostToDevice,cudaMemcpyDeviceToHost,cudaMemcpyDeviceToDevice};
struct cudaDeviceProp{char name[256]{};int concurrentKernels=0,multiProcessorCount=0;};
inline const char* cudaGetErrorString(CUresult e){const char* s=nullptr;DRV(cuGetErrorString,e,&s);return s?s:"unknown";}
inline CUresult cudaGetDeviceCount(int*p){native::init();return DRV(cuDeviceGetCount,p);}
inline CUresult cudaGetDeviceProperties(cudaDeviceProp*p,int){auto r=DRV(cuDeviceGetName,p->name,256,native::device);if(r)return r;r=DRV(cuDeviceGetAttribute,&p->concurrentKernels,CU_DEVICE_ATTRIBUTE_CONCURRENT_KERNELS,native::device);if(r)return r;return DRV(cuDeviceGetAttribute,&p->multiProcessorCount,CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT,native::device);}
inline CUresult cudaMemGetInfo(size_t*a,size_t*b){return DRVV(cuMemGetInfo,"cuMemGetInfo_v2",a,b);}
inline CUresult cudaMalloc(void**p,size_t n){CUdeviceptr v{};auto r=DRVV(cuMemAlloc,"cuMemAlloc_v2",&v,n);*p=reinterpret_cast<void*>(v);return r;}
inline CUresult cudaFree(void*p){return DRVV(cuMemFree,"cuMemFree_v2",reinterpret_cast<CUdeviceptr>(p));}
inline CUresult cudaMemset(void*p,int x,size_t n){return DRVV(cuMemsetD8,"cuMemsetD8_v2",reinterpret_cast<CUdeviceptr>(p),static_cast<unsigned char>(x),n);}
inline CUresult cudaMemsetAsync(void*p,int x,size_t n,CUstream s){return DRV(cuMemsetD8Async,reinterpret_cast<CUdeviceptr>(p),static_cast<unsigned char>(x),n,s);}
inline CUresult cudaMemcpy(void*to,const void*from,size_t n,CopyKind k){
 if(k==cudaMemcpyHostToDevice)return DRVV(cuMemcpyHtoD,"cuMemcpyHtoD_v2",reinterpret_cast<CUdeviceptr>(to),from,n);
 if(k==cudaMemcpyDeviceToHost)return DRVV(cuMemcpyDtoH,"cuMemcpyDtoH_v2",to,reinterpret_cast<CUdeviceptr>(from),n);
 return DRVV(cuMemcpyDtoD,"cuMemcpyDtoD_v2",reinterpret_cast<CUdeviceptr>(to),reinterpret_cast<CUdeviceptr>(from),n);
}
inline CUresult cudaMemcpyAsync(void*to,const void*from,size_t n,CopyKind k,CUstream s){
 if(k==cudaMemcpyHostToDevice)return DRVV(cuMemcpyHtoDAsync,"cuMemcpyHtoDAsync_v2",reinterpret_cast<CUdeviceptr>(to),from,n,s);
 if(k==cudaMemcpyDeviceToHost)return DRVV(cuMemcpyDtoHAsync,"cuMemcpyDtoHAsync_v2",to,reinterpret_cast<CUdeviceptr>(from),n,s);
 return DRVV(cuMemcpyDtoDAsync,"cuMemcpyDtoDAsync_v2",reinterpret_cast<CUdeviceptr>(to),reinterpret_cast<CUdeviceptr>(from),n,s);
}
inline CUresult cudaHostAlloc(unsigned**p,size_t n,unsigned flags){return DRV(cuMemHostAlloc,reinterpret_cast<void**>(p),n,flags);}
inline CUresult cudaFreeHost(void*p){return DRV(cuMemFreeHost,p);}
inline CUresult cudaDeviceGetStreamPriorityRange(int*a,int*b){return DRV(cuCtxGetStreamPriorityRange,a,b);}
inline CUresult cudaStreamCreateWithPriority(CUstream*p,unsigned flags,int priority){return DRV(cuStreamCreateWithPriority,p,flags,priority);}
inline CUresult cudaStreamDestroy(CUstream s){return DRVV(cuStreamDestroy,"cuStreamDestroy_v2",s);}
inline CUresult cudaStreamSynchronize(CUstream s){return DRV(cuStreamSynchronize,s);}
inline CUresult cudaDeviceSynchronize(){return DRV(cuCtxSynchronize);}
inline CUresult cudaStreamWaitEvent(CUstream s,CUevent e,unsigned flags){return DRV(cuStreamWaitEvent,s,e,flags);}
inline CUresult cudaEventCreateWithFlags(CUevent*p,unsigned flags){return DRV(cuEventCreate,p,flags);}
inline CUresult cudaEventRecord(CUevent e,CUstream s){return DRV(cuEventRecord,e,s);}
inline CUresult cudaEventQuery(CUevent e){return DRV(cuEventQuery,e);}
inline CUresult cudaEventSynchronize(CUevent e){return DRV(cuEventSynchronize,e);}
inline CUresult cudaEventElapsedTime(float*p,CUevent a,CUevent b){return DRV(cuEventElapsedTime,p,a,b);}
inline CUresult cudaEventDestroy(CUevent e){return DRVV(cuEventDestroy,"cuEventDestroy_v2",e);}
inline CUresult cudaGetLastError(){return CUDA_SUCCESS;} // cuLaunchKernel checked synchronously; async errors checked at sync.
