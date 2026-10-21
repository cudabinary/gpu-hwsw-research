"""Bounded host-only adaptation. CUDA kernel source and cubin remain unchanged."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'src/owner.cpp'
s=(ROOT/'input/base_owner.cpp').read_text()
s=s.replace('mode<=3&&g_->n()','mode<=6&&g_->n()')
s=s.replace('mode<2||(r_&&r_->graph_ptr().get()==g_.get())','r_&&r_->graph_ptr().get()==g_.get()')
s=s.replace('if(mode>=2){','if(r_){')  # Equal resident reverse and bitmap for all modes.
s=s.replace('if(mode_==3&&remaining==0)', 'if((mode_==4||mode_==5)&&fe==0){a.reason=4;break;}\n    if((mode_==3||mode_==5)&&remaining==0)')
s=s.replace('if(mode_>=2){\n     if(pull)', 'if(mode_>=2&&mode_!=6){\n     if(pull)')
cut=s.index('int main(int argc,char**argv)')
s=s[:cut]+(ROOT/'src/round_main.inc').read_text()
p.write_text(s)
