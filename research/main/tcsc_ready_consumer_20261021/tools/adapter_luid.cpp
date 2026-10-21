#define NOMINMAX
#include <windows.h>
#include <dxgi1_2.h>
#include <cstdio>
int main(){IDXGIFactory1* factory=nullptr;HRESULT h=CreateDXGIFactory1(__uuidof(IDXGIFactory1),reinterpret_cast<void**>(&factory));if(FAILED(h))return 1;unsigned found=0;
 for(unsigned i=0;;++i){IDXGIAdapter1*a=nullptr;h=factory->EnumAdapters1(i,&a);if(h==DXGI_ERROR_NOT_FOUND)break;if(FAILED(h))return 2;DXGI_ADAPTER_DESC1 d{};if(FAILED(a->GetDesc1(&d)))return 3;
 if(d.VendorId==0x10de){++found;std::printf("{\"vendor_id\":%u,\"device_id\":%u,\"luid\":\"0x%08x_0x%08x\",\"dedicated_video_bytes\":%llu}\n",d.VendorId,d.DeviceId,unsigned(d.AdapterLuid.HighPart),unsigned(d.AdapterLuid.LowPart),static_cast<unsigned long long>(d.DedicatedVideoMemory));}a->Release();}
 factory->Release();return found==1?0:4;}
