from pathlib import Path
import ctypes,subprocess,sys,os
from ctypes import wintypes as W
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
k.GetTickCount64.restype=ctypes.c_ulonglong
def now_tick():return k.GetTickCount64()
def start(child,status,deadline):
    c,e,kt,ut=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
    if not k.GetProcessTimes(W.HANDLE(int(child._handle)),ctypes.byref(c),ctypes.byref(e),ctypes.byref(kt),ctypes.byref(ut)):raise RuntimeError('child creation unavailable')
    return subprocess.Popen([sys.executable,str(Path(__file__).with_name('child_watchdog.py')),
        '--child',str(child.pid),'--parent',str(os.getpid()),'--created',str((c.dwHighDateTime<<32)|c.dwLowDateTime),
        '--deadline',str(deadline),'--status',str(status)],creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
