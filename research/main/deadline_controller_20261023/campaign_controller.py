"""Whole-pipeline deadline owner. This revision dispatches CPU fixtures ONLY.

The production GPU adapter remains explicitly disabled pending a new allocation.
Deadline correctness is checked before/after every adapter call, including start,
poll, reap and artifact production. OS stalls cannot be given a hard realtime
guarantee: a late return is FAILED, never retroactively called within-budget.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json,time,subprocess,sys,os

PHASES=('execution','postprocess','package')
GPU_EXECUTION_ENABLED=False
@dataclass(frozen=True)
class Budget:
 total:float
 execution:float
 postprocess:float
 package:float
 shutdown_reserve:float
 def __post_init__(self):
  vals=[self.total,self.execution,self.postprocess,self.package,self.shutdown_reserve]
  if any(v<=0 or not __import__('math').isfinite(v) for v in vals):raise ValueError('INVALID_BUDGET')
  if sum(vals[1:])>self.total+1e-9:raise ValueError('PHASE_CAPS_PLUS_RESERVE_EXCEED_TOTAL')
 def cap(self,p):return getattr(self,p)

@dataclass(frozen=True)
class Stage:
 name:str
 phase:str
 timeout:float
 fixture:str='ok'
 required:bool=True
 def __post_init__(self):
  if self.phase not in PHASES or self.timeout<=0:raise ValueError('INVALID_STAGE')

class RealClock:
 def now(self):return time.monotonic()
 def wait(self,seconds):time.sleep(seconds)

class CPUHandle:
 def __init__(self,p,stdout,stderr):self.p=p;self.stdout=stdout;self.stderr=stderr;self.closed=False
 def poll(self):return self.p.poll()
 def stop(self):
  if self.p.poll() is None:self.p.terminate()
 def reap(self,timeout):
  try:self.p.wait(timeout=max(0,timeout))
  except subprocess.TimeoutExpired:return False
  self.stdout.close();self.stderr.close();self.closed=True;return True

class CPUBackend:
 """Only a fixed local fixture script can be launched; no arbitrary argv."""
 def __init__(self,directory):self.d=Path(directory);self.children=[];self.issued=[]
 def start(self,stage):
  if stage.fixture not in ('ok','fail','hang'):raise ValueError('CPU_FIXTURE_ALLOWLIST')
  script=Path(__file__).with_name('cpu_fixture.py').absolute()
  out=(self.d/(stage.name+'.stdout')).open('xb');err=(self.d/(stage.name+'.stderr')).open('xb')
  args=[sys.executable,'-B',str(script),stage.fixture]
  p=subprocess.Popen(args,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  h=CPUHandle(p,out,err);self.children.append(h);self.issued.append({'name':stage.name,'pid':p.pid,'argv':args});return h

class GPUBackend:
 def start(self,stage):raise RuntimeError('GPU_ADAPTER_DISABLED_NO_NEW_ALLOCATION')

class Campaign:
 def __init__(self,budget,backend,clock):
  self.b=budget;self.backend=backend;self.clock=clock;self.epoch=None;self.events=[];self.phase_used=dict.fromkeys(PHASES,0.);self.reason=None;self.owned_exit=True;self.closed=False;self.execution_end=None
 def elapsed(self):return self.clock.now()-self.epoch
 def event(self,kind,**data):self.events.append({'event':kind,'elapsed':self.elapsed(),**data})
 def fail(self,reason):
  if self.reason is None:self.reason=reason
  self.event('FAIL',reason=reason)
 def stop_and_reap(self,h):
  self.event('OWNED_STOP_REQUEST');h.stop()
  left=max(0.,self.b.total-self.elapsed())
  self.owned_exit=h.reap(left)
  if not self.owned_exit:self.fail('OWNED_EXIT_UNKNOWN')
  self.event('OWNED_REAP',exit_observed=self.owned_exit)
 def run(self,stages):
  if self.epoch is not None:raise RuntimeError('CAMPAIGN_CANNOT_RESTART')
  self.epoch=self.clock.now();self.event('START',total=self.b.total)
  order=[PHASES.index(s.phase) for s in stages]
  if order!=sorted(order):self.fail('PHASE_ORDER');return self.finish()
  for s in stages:
   if s.phase!='execution' and self.execution_end is None:
    self.execution_end=self.elapsed();self.event('EXECUTION_PHASE_ENDED')
   if self.reason is not None:break
   if not s.required:self.event('SKIP_OPTIONAL',stage=s.name);continue
   remaining_phase=self.b.cap(s.phase)-self.phase_used[s.phase]
   remaining_total=self.b.total-self.b.shutdown_reserve-self.elapsed()
   if s.timeout>remaining_phase+1e-9 or s.timeout>remaining_total+1e-9:
    self.fail('INSUFFICIENT_BUDGET_BEFORE_START');break
   before=self.clock.now();h=None;deadline=before+s.timeout
   self.event('START_STAGE',stage=s.name,phase=s.phase,deadline_at=deadline-self.epoch)
   try:
    h=self.backend.start(s)
    # Launch itself may block; never acknowledge a late launch as success.
    while True:
     if self.clock.now()>=deadline or self.elapsed()>=self.b.total-self.b.shutdown_reserve:
      self.fail('STAGE_OR_WORK_DEADLINE');self.stop_and_reap(h);break
     rc=h.poll()
     if self.clock.now()>=deadline or self.elapsed()>=self.b.total-self.b.shutdown_reserve:
      self.fail('BLOCKING_OBSERVATION_RETURNED_LATE');self.stop_and_reap(h);break
     if rc is not None:
      if not h.reap(min(self.b.shutdown_reserve,max(0.,self.b.total-self.elapsed()))):
       self.owned_exit=False;self.fail('OWNED_EXIT_UNKNOWN')
      if rc!=0:self.fail('CHILD_FAILURE')
      break
     self.clock.wait(min(.01,max(0.,deadline-self.clock.now()),max(0.,self.b.total-self.b.shutdown_reserve-self.elapsed())))
   except BaseException as e:
    self.fail('ADAPTER_ERROR:'+type(e).__name__+':'+str(e))
    if h is not None:self.stop_and_reap(h)
   finally:
    self.phase_used[s.phase]+=self.clock.now()-before
    self.event('END_STAGE',stage=s.name,phase=s.phase,owned_exit=self.owned_exit)
    if self.clock.now()>deadline+1e-9 and self.reason is None:self.fail('STAGE_RETURNED_LATE')
   if self.phase_used[s.phase]>self.b.cap(s.phase)+1e-9 and self.reason is None:self.fail('PHASE_BUDGET_EXCEEDED')
   if self.elapsed()>self.b.total and self.reason is None:self.fail('TOTAL_DEADLINE_EXCEEDED')
  return self.finish()
 def finish(self):
  if self.closed:raise RuntimeError('ALREADY_CLOSED')
  self.closed=True
  if self.execution_end is None:self.execution_end=self.elapsed()
  elapsed=self.elapsed()
  if elapsed>self.b.total:self.fail('TOTAL_DEADLINE_EXCEEDED')
  status='CLOSED_PASS' if self.reason is None and self.owned_exit and elapsed<=self.b.total else ('HOLD_EXIT_UNKNOWN' if not self.owned_exit else 'CLOSED_FAILED')
  self.event('CLOSE',status=status)
  return {'status':status,'reason':self.reason,'elapsed':self.elapsed(),'total':self.b.total,'phase_used':self.phase_used,'execution_phase_end':self.execution_end,'owned_exit_observed':self.owned_exit,'GPU_calls':0,'CPU_fixture_only':True,'events':self.events,'no_resume_no_budget_reset':True}

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--case',choices=['normal','failure','hang'],required=True);p.add_argument('--output',required=True);p.add_argument('--run-gpu',action='store_true');a=p.parse_args()
 d=Path(a.output);d.mkdir(parents=True,exist_ok=False)
 # Exclusive intent is created before dispatch; a result directory cannot be reused.
 (d/'START_INTENT.json').write_text(json.dumps({'case':a.case,'UTC_ns':time.time_ns(),'source_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'GPU_enabled':GPU_EXECUTION_ENABLED}))
 if a.run_gpu:
  (d/'REJECTED.json').write_text(json.dumps({'reason':'GPU_ADAPTER_DISABLED_NO_NEW_ALLOCATION','child_launches':0,'GPU_queries':0}));return 3
 b=Budget(2.4,.9,.5,.4,.6);backend=CPUBackend(d)
 stages=[Stage('execute','execution',.6,'hang' if a.case=='hang' else ('fail' if a.case=='failure' else 'ok')),Stage('analyze','postprocess',.4),Stage('package','package',.3)]
 clock=RealClock();controller=Campaign(b,backend,clock);x=controller.run(stages);x['children']=backend.issued
 # Receipt write is included in the observed total; if the write itself returns
 # too late its final receipt is failed. Unbounded OS I/O remains a stated limit.
 q=d/'RESULT.json';x['elapsed_before_receipt_write']=controller.elapsed();q.write_text(json.dumps(x,indent=2)+'\n')
 x['elapsed_after_first_receipt_write']=controller.elapsed()
 if x['elapsed_after_first_receipt_write']>b.total:x.update(status='CLOSED_FAILED',reason='RECEIPT_WRITE_RETURNED_AFTER_TOTAL')
 x['final_metadata_write_has_no_hard_realtime_OS_guarantee']=True
 q.write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps({'status':x['status'],'elapsed':x['elapsed'],'children':len(backend.children),'GPU_calls':0}))
 return 0 if x['status']=='CLOSED_PASS' else 2
if __name__=='__main__':raise SystemExit(main())
