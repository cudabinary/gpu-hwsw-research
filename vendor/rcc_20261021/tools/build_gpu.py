import pathlib,subprocess,time,json,hashlib,os
P=pathlib.Path(__file__).resolve().parents[1];os.chdir(P)
prior=P.parent/'V05_GPU_EXECUTION_R1_20261020/include/native_driver.hpp'
data=prior.read_bytes();(P/'cuda/native_driver.hpp').write_bytes(data)
pathlib.Path('audit/NATIVE_DRIVER_PROVENANCE.json').write_text(json.dumps(dict(path=str(prior),sha256=hashlib.sha256(data).hexdigest(),unchanged=True),indent=2))
def run(tag,cmd):
    assert not pathlib.Path('results',tag+'.json').exists(),'no overwrite'
    t=time.time()
    p=subprocess.run(cmd,capture_output=True,timeout=180)
    pathlib.Path('results',tag+'.stdout.log').write_bytes(p.stdout);pathlib.Path('results',tag+'.stderr.log').write_bytes(p.stderr)
    pathlib.Path('results',tag+'.json').write_text(json.dumps(dict(command=cmd,exit_code=p.returncode,seconds=time.time()-t,GPU_kernels=0),indent=2))
    print(tag,p.returncode,flush=True)
    if p.returncode:raise SystemExit(p.returncode)
nv='/usr/local/cuda-13.3/bin/nvcc'
run('gpu_static_ptx',[nv,'-std=c++17','-O2','-arch=sm_89','-Icuda','--ptx','cuda/kernels.cu','-o','build/rcc_kernels.ptx'])
run('gpu_static_cubin',[nv,'-std=c++17','-O2','-arch=sm_89','-Icuda','--cubin','-Xptxas=-v','cuda/kernels.cu','-o','build/rcc_kernels.cubin'])
run('gpu_static_native',['x86_64-w64-mingw32-g++','-std=c++17','-O2','-static','-Icuda','-Ifrozen/consumer','-I/usr/local/cuda-13.3/include','cuda/owner.cpp','-o','build/rcc_owner.exe'])
pathlib.Path('build/abi.cpp').write_text('#include "abi.hpp"\n#include <iostream>\nint main(){using namespace rgpu;std::cout<<"{\\"View\\":"<<sizeof(View)<<",\\"Counter\\":"<<sizeof(Counter)<<",\\"row\\":"<<offsetof(View,row)<<",\\"counter\\":"<<offsetof(View,counter)<<"}\\n";}')
run('gpu_abi_linux_compile',['g++','-std=c++17','-Icuda','build/abi.cpp','-o','build/abi_linux'])
run('gpu_abi_linux',['build/abi_linux'])
