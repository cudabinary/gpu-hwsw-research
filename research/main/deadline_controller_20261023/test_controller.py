from pathlib import Path
import json,sys,subprocess,time,hashlib
from campaign_controller import Budget,Stage,Campaign
R=Path(__file__).absolute().parent
class Clock:
 def __init__(self):self.t=0.
 def now(self):return self.t
 def wait(self,x):self.t+=x
class Handle:
 def __init__(self,b,stage):self.b=b;self.start=b.clock.now();self.stage=stage;self.stopped=False
 def poll(self):
  if self.b.poll_stall:self.b.clock.wait(self.b.poll_stall);self.b.poll_stall=0.
  return self.b.rc if self.b.clock.now()-self.start>=self.b.durations[self.stage.name] else None
 def stop(self):self.stopped=True
 def reap(self,left):
  delay=min(self.b.reap_delay,left);self.b.clock.wait(delay)
  return self.b.exit_known
class Backend:
 def __init__(self,clock,durations,rc=0,exit_known=True,start_delay=0.,poll_stall=0.,reap_delay=0.,error=None):
  self.clock=clock;self.durations=durations;self.rc=rc;self.exit_known=exit_known;self.start_delay=start_delay;self.poll_stall=poll_stall;self.reap_delay=reap_delay;self.error=error;self.started=[]
 def start(self,s):
  self.started.append(s.name);self.clock.wait(self.start_delay)
  if self.error:raise self.error
  return Handle(self,s)
rows=[]
def check(name,durations,budget,stages,expected,started=None,**kwargs):
 c=Clock();b=Backend(c,durations,**kwargs);owner=Campaign(budget,b,c);x=owner.run(stages)
 assert x['status']==expected,(name,x)
 if started is not None:assert b.started==started,(name,b.started)
 if expected=='CLOSED_PASS':assert x['elapsed']<=budget.total and x['owned_exit_observed']
 try:owner.run(stages)
 except RuntimeError as e:assert str(e)=='CAMPAIGN_CANNOT_RESTART'
 else:raise AssertionError('budget reset allowed')
 rows.append({'name':name,'PASS':True,'result':x,'started':b.started})
b=Budget(2.4,.9,.5,.4,.6);st=[Stage('e','execution',.8),Stage('p','postprocess',.4),Stage('z','package',.3)]
check('all_phases_same_deadline',{'e':.1,'p':.1,'z':.1},b,st,'CLOSED_PASS')
check('execution_overrun_stops_pipeline',{'e':10,'p':.1,'z':.1},b,st,'CLOSED_FAILED',['e'])
check('postprocess_overrun_stops_package',{'e':.1,'p':10,'z':.1},b,st,'CLOSED_FAILED',['e','p'])
check('package_overrun_is_failure',{'e':.1,'p':.1,'z':10},b,st,'CLOSED_FAILED',['e','p','z'])
check('optional_compare_not_started',{'e':.1,'p':.1,'z':.1},b,[st[0],Stage('unused','execution',.1,required=False),st[1],st[2]],'CLOSED_PASS',['e','p','z'])
check('unknown_exit_latches_hold',{'e':.1},b,st,'HOLD_EXIT_UNKNOWN',['e'],exit_known=False)
check('nonzero_exit_no_next_stage',{'e':.1},b,st,'CLOSED_FAILED',['e'],rc=7)
check('late_start_is_not_success',{'e':.1},b,st,'CLOSED_FAILED',['e'],start_delay=2.)
check('blocking_observation_is_not_success',{'e':.1},b,st,'CLOSED_FAILED',['e'],poll_stall=3.)
check('metadata_exception_closes_without_followup',{'e':.1},b,st,'CLOSED_FAILED',['e'],error=KeyError('allocated_after_cleanup'))
check('invalid_phase_order_no_launch',{'e':.1},b,list(reversed(st)),'CLOSED_FAILED',[])
check('phase_limit_rejects_before_launch',{'e':.1},b,[Stage('e','execution',1.1)],'CLOSED_FAILED',[])
# Original timeline reproduced as work durations under unchanged future240 cap.
big=Budget(240,120,60,40,20)
check('legacy318s_sequence_fails_in_post_before_package',{'e':85.8203853,'p':120.7855536,'z':112.1409698},big,[Stage('e','execution',110),Stage('p','postprocess',60),Stage('z','package',40)],'CLOSED_FAILED',['e','p'])
for total,ex,post,pack,res in [(240,120,60,40,20),(120,55,30,20,15),(24,12,6,4,2),(2.4,.9,.5,.4,.6)]:
 cap=Budget(total,ex,post,pack,res)
 check('scaled_budget_'+str(total),{'e':ex*.1,'p':post*.1,'z':pack*.1},cap,[Stage('e','execution',ex*.8),Stage('p','postprocess',post*.8),Stage('z','package',pack*.8)],'CLOSED_PASS')
for args in [(240,120,60,60,20),(0,1,1,1,1),(1,float('nan'),.1,.1,.1)]:
 try:Budget(*args)
 except ValueError:rows.append({'name':'invalid_budget_'+str(args),'PASS':True})
 else:raise AssertionError('invalid budget accepted')
# The actual CLI, actual subprocess backend and owned terminate/reap paths.
# Three parent CLIs +five small CPU children total; no Torch/NVIDIA API import.
start=time.monotonic();actual=[]
for case,rc,children in [('normal',0,3),('failure',2,1),('hang',2,1),('gpu_rejected',3,0)]:
 d=R/'cpu_runs'/case;argv=[sys.executable,'-B',str(R/'campaign_controller.py'),'--case',case if case!='gpu_rejected' else 'normal','--output',str(d)]
 if case=='gpu_rejected':argv+=['--run-gpu']
 p=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=4)
 assert p.returncode==rc,(case,p.stdout,p.stderr)
 (R/(case+'.stdout.log')).write_text(p.stdout);(R/(case+'.stderr.log')).write_text(p.stderr)
 if case=='gpu_rejected':x=json.loads((d/'REJECTED.json').read_text());assert x['child_launches']==x['GPU_queries']==0
 else:
  x=json.loads((d/'RESULT.json').read_text());assert len(x['children'])==children and x['owned_exit_observed'];assert x['elapsed_after_first_receipt_write']<=2.4
  if case=='hang':assert any(e['event']=='OWNED_STOP_REQUEST' for e in x['events'])
 actual.append({'case':case,'returncode':p.returncode,'children':children,'PASS':True,'receipt':x})
assert time.monotonic()-start<15
out={'PASS':True,'CPU_only':True,'GPU_queries_loads_executions':0,'fake_clock_cases':rows,'actual_CLI_cases':actual,'actual_CPU_child_processes':5,'actual_fixture_CLI_processes':4,'elapsed_actual_CLI_checks_seconds':time.monotonic()-start,'limitations':'No GPU adapter execution/certification. OS suspend, uninterruptible subprocess creation or I/O can return after a deadline; those are failed/unknown, not guaranteed realtime completion. Previous318.7469s violation unchanged.'}
(R/'CPU_CONTROLLER_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'PASS':True,'mock_cases':len(rows),'actual_CLI_cases':len(actual),'CPU_children':5,'GPU_calls':0}))
