"""Read-only WSL compute-module check. No CUDA API or GPU query."""
from pathlib import Path
import argparse,json,os,re,time
p=argparse.ArgumentParser();p.add_argument('--status',required=True);p.add_argument('--stop',required=True);a=p.parse_args()
status=Path(a.status);stop=Path(a.stop)
while not stop.exists():
    compute=[];unreadable=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
        try:
            executable=(proc/'comm').read_text().strip()
            maps=(proc/'maps').read_text()
            modules=sorted(set(re.findall(r'/(lib(?:cuda|cudart|cublas|cusparse|torch_cuda|nvidia-ptxjitcompiler)[^/\s]*)',maps)))
            if modules:compute.append({'pid':int(proc.name),'name':executable,'modules':modules})
        except FileNotFoundError:continue
        except PermissionError:
            try:
                name=(proc/'comm').read_text().strip()
                if re.search('python|cuda|nvcc|nsys|ncu|gpu|align|bfs|torch',name,re.I):unreadable.append({'pid':int(proc.name),'name':name})
            except OSError:pass
    result={'status':'OK' if not compute and not unreadable else 'BLOCKED','epoch_ms':int(time.time()*1000),
            'compute_processes':compute,'unreadable_potential_compute':unreadable,'cuda_api_calls':0}
    tmp=status.with_suffix('.tmp');tmp.write_text(json.dumps(result));os.replace(tmp,status)
    if result['status']!='OK':raise SystemExit(1)
    time.sleep(.5)
