from pathlib import Path
import json,subprocess,sys
import watchdog_support as w
R=Path(__file__).resolve().parents[1];rows=[]
for label,delay,budget,expected in [('normal',.05,3000,'CHILD_EXITED'),('timeout',2,.3*1000,'DEADLINE_CHILD_TERMINATED')]:
    child=subprocess.Popen([sys.executable,'-c','import time;time.sleep('+str(delay)+')'],creationflags=subprocess.CREATE_NO_WINDOW)
    status=R/'audit'/('watchdog_test_'+label+'.json')
    guard=w.start(child,status,w.now_tick()+int(budget));guard.wait(timeout=5);child.wait(timeout=3)
    result=json.loads(status.read_text());rows.append({'test':label,'pass':result['status']==expected,'state':result,'child_exit_code':child.returncode})
report={'status':'PASS' if all(x['pass'] for x in rows) else 'FAIL','GPU_calls':0,'only_disposable_owned_children':True,'cases':rows}
(R/'audit/WATCHDOG_TEST.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert report['status']=='PASS'
