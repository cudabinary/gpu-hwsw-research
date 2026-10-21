"""Generate a new host version from frozen inputs; never edit the old owner."""
from pathlib import Path
import difflib,hashlib,json,shutil
R=Path(__file__).resolve().parents[1];OLD=R.parent
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    target=R/'src/owner_controls_v1.cpp'
    if target.exists():raise RuntimeError('PRESERVE_EXISTING_GENERATED_VERSION')
    pins=json.loads((OLD/'config/SOURCE_BINARY_INPUT_PINS.json').read_text())['pins']
    for name,digest in pins.items():assert sha((OLD/name).read_bytes())==digest,name
    for folder in ['include','build','audit','config']:(R/folder).mkdir(exist_ok=True)
    for rel in ['src/abi.hpp','src/native_driver.hpp','src/kernels.cu','include/independent_builder.hpp','build/rcc_kernels.cubin']:
        dest=R/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/rel,dest)
    s=(OLD/'src/owner.cpp').read_text()
    def replace(before,after,expected=1):
        nonlocal s
        if s.count(before)!=expected:raise RuntimeError('FROZEN_ANCHOR_MISMATCH_'+before[:60])
        s=s.replace(before,after)
    replace('#include "abi.hpp"','#include "abi.hpp"\n#include "host_controls.hpp"')
    replace('bool failed_=false;','bool failed_=false;host_control::IncomingBound incoming_bound_;double bound_setup_ms_=0;')
    replace('require(mode<=6&&g_->n()','require(host_control::supported(mode)&&g_->n()')
    replace('ck(cudaStreamCreateWithPriority(&stream_,cudaStreamNonBlocking,0));',
      'auto bound_start=Clock::now();incoming_bound_=host_control::IncomingBound::prepare(*g_,*r_);bound_setup_ms_=milliseconds(bound_start);\n   ck(cudaStreamCreateWithPriority(&stream_,cudaStreamNonBlocking,0));')
    replace('a.bound=mode_==1?table_[source]:d_.n;',
      'a.bound=host_control::static_bound_mode(mode_)?incoming_bound_.limit(*g_,*r_,source):d_.n;')
    replace('L remaining=mode_>=2?','L remaining=host_control::degree_stats(mode_)?')
    old='''if(a.seen==d_.n){a.reason=1;break;}
    if((mode_==4||mode_==5)&&fe==0){a.reason=4;break;}
    if((mode_==3||mode_==5)&&remaining==0){a.reason=2;break;}'''
    # The generated owner preserves the source's original indentation.
    actual='\n'.join(x.strip() for x in old.splitlines())
    original='\n'.join(x.strip() for x in s.splitlines())
    if actual not in original:raise RuntimeError('STOP_SEQUENCE_ANCHOR')
    replace('if(a.seen==d_.n){a.reason=1;break;}\n    if((mode_==4||mode_==5)&&fe==0){a.reason=4;break;}\n    if((mode_==3||mode_==5)&&remaining==0){a.reason=2;break;}',
      'if(U reason=host_control::stop(mode_,a.seen,d_.n,fe,remaining,a.bound)){a.reason=reason;break;}')
    replace('if(mode_>=2&&mode_!=6){','if(host_control::direction(mode_)){')
    replace('U(mode_>=2)','U(host_control::degree_stats(mode_))')
    replace('if(mode_>=2){require(c.in_edges','if(host_control::degree_stats(mode_)){require(c.in_edges')
    replace('size_t bytes()const{return arena_.bytes;}',
      'size_t bytes()const{return arena_.bytes;}\n  double bound_setup_ms()const{return bound_setup_ms_;}')
    replace('Replay a;a.d.assign(g.n(),-1);',
      'auto metadata=host_control::IncomingBound::prepare(g,r);U bound=host_control::static_bound_mode(mode)?metadata.limit(g,r,source):g.n();\n Replay a;a.d.assign(g.n(),-1);')
    replace('if(a.seen==g.n()){a.reason=1;break;}\n  if((mode==4||mode==5)&&fe==0){a.reason=4;break;}\n  if((mode==3||mode==5)&&remaining==0){a.reason=2;break;}',
      'if(U reason=host_control::stop(mode,a.seen,g.n(),fe,remaining,bound)){a.reason=reason;break;}')
    replace('if(mode>=2&&mode!=6){','if(host_control::direction(mode)){')
    replace('if(mode>=2){next_out','if(host_control::degree_stats(mode)){next_out')
    replace('if(mode>=2){require(next_in','if(host_control::degree_stats(mode)){require(next_in')
    replace('int main(int argc,char**argv){try{',
      '#include "targeted_tests.inc"\nint main(int argc,char**argv){try{\n if(argc==2&&std::string(argv[1])=="--control-tests")return control_tests();')
    replace('(mode==0||(mode>=2&&mode<=6))','host_control::supported(mode)')
    replace('auto setup_start=Clock::now();native::init();',
      'require(native::dll==nullptr,"unexpected driver before controls gate");\n const char*control_permit=std::getenv("TCSC_HOST_CONTROLS_V1_APPROVED");\n require(control_permit&&std::string(control_permit)=="NEW_REVIEWED_FINITE_PLAN","HOLD_ENVIRONMENT: fresh controls plan required");\n auto setup_start=Clock::now();native::init();')
    replace('std::cerr<<"STOP_NO_RETRY "<<e.what()<<"\\n";',
      'std::cerr<<"STOP_NO_RETRY "<<e.what()<<" driver_loaded="<<(native::dll?1:0)<<" kernels="<<native::launched<<"\\n";')
    replace('<<a.remaining<<',
      '<<a.remaining<<",\\\"remaining_in_known\\\":"<<(host_control::degree_stats(mode)?"true":"false")<<",\\\"visit_bound\\\":"<<a.bound<<')
    replace('<<owner.bytes()<<',
      '<<owner.bytes()<<",\\\"static_bound_setup_ms\\\":"<<owner.bound_setup_ms()<<')
    target.write_text(s)
    patch=''.join(difflib.unified_diff((OLD/'src/owner.cpp').read_text().splitlines(True),s.splitlines(True),fromfile='frozen/src/owner.cpp',tofile='host_controls_v1/src/owner_controls_v1.cpp'))
    (R/'audit/HOST_ONLY_DIFF.patch').write_text(patch)
    changed=sum(x.startswith(('+','-')) and not x.startswith(('+++','---')) for x in patch.splitlines())
    if changed>100:raise RuntimeError('HOST_CHANGE_TOO_LARGE_STOP_BEFORE_BUILD')
    (R/'audit/SOURCE_PROVENANCE.json').write_text(json.dumps({'frozen_owner_sha256':pins['src/owner.cpp'],
      'new_owner_sha256':sha(target.read_bytes()),'changed_diff_lines':changed,
      'unchanged_copies':{rel:sha((R/rel).read_bytes()) for rel in ['src/abi.hpp','src/native_driver.hpp','src/kernels.cu','include/independent_builder.hpp','build/rcc_kernels.cubin']},
      'GPU_calls':0,'old_source_or_results_modified':False},indent=2))
    print(json.dumps({'changed_host_diff_lines':changed,'new_owner_sha256':sha(target.read_bytes()),'kernel_changed':False}))
if __name__=='__main__':main()
