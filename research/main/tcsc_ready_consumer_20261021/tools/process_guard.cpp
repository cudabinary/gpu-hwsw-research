#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include <algorithm>
#include <cwctype>
#include <iostream>
#include <string>
#include <vector>
int main(int argc,char**argv){
 std::cout<<"{\"status\":\"OK\",\"checked\":[";bool comma=false;
 for(int k=1;k<argc;++k){DWORD pid=std::stoul(argv[k]);HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ,FALSE,pid);
  if(!process){if(GetLastError()==ERROR_INVALID_PARAMETER)continue;std::cerr<<"module access unavailable PID "<<pid;return 2;}
  FILETIME created{},exited{},kernel{},user{};if(!GetProcessTimes(process,&created,&exited,&kernel,&user)){CloseHandle(process);return 3;}
  std::vector<HMODULE> modules(2048);DWORD bytes=0;
  if(!EnumProcessModulesEx(process,modules.data(),DWORD(modules.size()*sizeof(HMODULE)),&bytes,LIST_MODULES_ALL)||!bytes||bytes>modules.size()*sizeof(HMODULE)){CloseHandle(process);return 4;}
  unsigned count=bytes/sizeof(HMODULE);
  for(unsigned i=0;i<count;++i){wchar_t buf[1024]{};if(!GetModuleBaseNameW(process,modules[i],buf,1024)){CloseHandle(process);return 5;}std::wstring name(buf);std::transform(name.begin(),name.end(),name.begin(),[](wchar_t c){return std::towlower(c);});
   for(const wchar_t* prefix:{L"nvcuda",L"cudart",L"cublas",L"cudnn",L"cusparse",L"nvrtc",L"directml",L"torch",L"onnxruntime"})if(name.rfind(prefix,0)==0){std::cerr<<"compute module PID "<<pid;CloseHandle(process);return 6;}}
  CloseHandle(process);unsigned long long timestamp=(static_cast<unsigned long long>(created.dwHighDateTime)<<32)|created.dwLowDateTime;
  std::cout<<(comma?",":"")<<"{\"pid\":"<<pid<<",\"creation_filetime\":"<<timestamp<<",\"modules\":"<<count<<"}";comma=true;
 }
 std::cout<<"]}\n";
}
