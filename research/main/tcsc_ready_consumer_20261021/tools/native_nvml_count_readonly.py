"""One native public NVML count probe; no process-memory or CUDA execution APIs.

The official NULL-info count call avoids guessing nvmlProcessInfo structure ABI.
No existing guard is imported or modified. No compute/driver mode is set.
"""
from pathlib import Path
import ctypes as C,datetime as dt,json,os

def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
r={'started_utc':utc(),'scope':'NATIVE_WINDOWS_NVML_PUBLIC_READ_ONLY','own_pid':os.getpid(),
   'process_memory_or_module_queries':0,'CUDA_execution_APIs_called':0,'configuration_changes':0,
   'compute_record_array_requested':False,'measurement_isolation_proved':False,'benchmark_resume_allowed':False,'calls':[]}
try:
    dll=C.WinDLL(r'C:\Windows\System32\nvml.dll',winmode=0x00000800)
    def fn(name,args,result=C.c_int):
        f=getattr(dll,name);f.argtypes=args;f.restype=result;return f
    err=fn('nvmlErrorString',[C.c_int],C.c_char_p)
    def call(name,f,*args):
        code=int(f(*args));text=err(code)
        r['calls'].append({'api':name,'code':code,'meaning':text.decode(errors='replace') if text else None,'utc':utc()})
        return code
    init=fn('nvmlInit_v2',[]);shutdown=fn('nvmlShutdown',[])
    code=call('nvmlInit_v2',init)
    if code!=0:r['status']='INITIALIZATION_UNAVAILABLE'
    else:
        try:
            for symbol,field in [('nvmlSystemGetDriverVersion','driver_version'),('nvmlSystemGetNVMLVersion','nvml_version')]:
                buf=C.create_string_buffer(128);f=fn(symbol,[C.c_void_p,C.c_uint])
                if call(symbol,f,buf,len(buf))==0:r[field]=buf.value.decode(errors='replace')
            count=C.c_uint();f=fn('nvmlDeviceGetCount_v2',[C.POINTER(C.c_uint)])
            if call('nvmlDeviceGetCount_v2',f,C.byref(count))!=0 or count.value!=1:
                r['status']='DEVICE_COUNT_UNAVAILABLE_OR_AMBIGUOUS';r['device_count']=count.value
            else:
                device=C.c_void_p();get=fn('nvmlDeviceGetHandleByIndex_v2',[C.c_uint,C.POINTER(C.c_void_p)])
                if call('nvmlDeviceGetHandleByIndex_v2',get,0,C.byref(device))!=0:r['status']='DEVICE_HANDLE_UNAVAILABLE'
                else:
                    name=C.create_string_buffer(128);n=fn('nvmlDeviceGetName',[C.c_void_p,C.c_void_p,C.c_uint])
                    if call('nvmlDeviceGetName',n,device,name,len(name))==0:r['device_name']=name.value.decode(errors='replace')
                    query=fn('nvmlDeviceGetComputeRunningProcesses_v3',[C.c_void_p,C.POINTER(C.c_uint),C.c_void_p])
                    entries=C.c_uint(0);code=call('nvmlDeviceGetComputeRunningProcesses_v3_NULL_count',query,device,C.byref(entries),None)
                    r['compute_count_result']={'return_code':code,'required_entries':entries.value,
                       'query_supported_at_this_call':code in (0,7),
                       'classification':'SNAPSHOT_EMPTY' if code==0 and entries.value==0 else 'COMPUTE_CONTEXTS_REPORTED' if code==7 and entries.value>0 else 'UNKNOWN'}
                    r['status']='READ_ONLY_PROBE_COMPLETE'
        finally:call('nvmlShutdown',shutdown)
except (OSError,AttributeError) as exc:
    r['status']='DLL_OR_SYMBOL_UNAVAILABLE';r['error_type']=type(exc).__name__
r['ended_utc']=utc();print(json.dumps(r),flush=True)
