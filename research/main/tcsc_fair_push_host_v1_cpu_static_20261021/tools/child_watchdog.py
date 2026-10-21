"""Independent Windows watchdog for one PID+creation-time pinned owned child."""
from pathlib import Path
import argparse,ctypes,json,os
from ctypes import wintypes as W
p=argparse.ArgumentParser();p.add_argument('--child',type=int,required=True);p.add_argument('--parent',type=int,required=True);p.add_argument('--created',type=int,required=True);p.add_argument('--deadline',type=int,required=True);p.add_argument('--status',required=True);a=p.parse_args()
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
k.GetTickCount64.restype=ctypes.c_ulonglong
k.WaitForMultipleObjects.argtypes=[W.DWORD,ctypes.POINTER(W.HANDLE),W.BOOL,W.DWORD];k.WaitForMultipleObjects.restype=W.DWORD
k.TerminateProcess.argtypes=[W.HANDLE,W.UINT];k.CloseHandle.argtypes=[W.HANDLE]
status=Path(a.status)
def save(state):
    tmp=status.with_suffix('.tmp');tmp.write_text(json.dumps({'status':state,'child':a.child,'parent':a.parent,'deadline_tick_ms':a.deadline}));os.replace(tmp,status)
child=k.OpenProcess(0x00100000|0x1000|0x0001,False,a.child)
parent=k.OpenProcess(0x00100000,False,a.parent)
if not child or not parent:save('HANDLE_UNAVAILABLE');raise SystemExit(2)
try:
    c,e,kt,ut=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
    if not k.GetProcessTimes(child,ctypes.byref(c),ctypes.byref(e),ctypes.byref(kt),ctypes.byref(ut)) or ((c.dwHighDateTime<<32)|c.dwLowDateTime)!=a.created:
        save('CHILD_IDENTITY_MISMATCH');raise SystemExit(2)
    save('WATCHING')
    handles=(W.HANDLE*2)(child,parent)
    result=k.WaitForMultipleObjects(2,handles,False,max(0,a.deadline-k.GetTickCount64()))
    if result==0:save('CHILD_EXITED')
    elif result in (1,258):
        k.TerminateProcess(child,124);save('PARENT_EXITED_CHILD_TERMINATED' if result==1 else 'DEADLINE_CHILD_TERMINATED');raise SystemExit(1)
    else:save('WAIT_FAILED');raise SystemExit(2)
finally:k.CloseHandle(child);k.CloseHandle(parent)
