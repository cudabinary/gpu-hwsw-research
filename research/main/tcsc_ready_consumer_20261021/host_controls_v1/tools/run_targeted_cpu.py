"""One targeted CPU run plus one no-permit boundary rejection. No GPU APIs."""
from pathlib import Path
import json,os,subprocess,time
R=Path(__file__).resolve().parents[1]
if (R/'audit/CPU_TARGETED_RESULT.json').exists():raise RuntimeError('PRESERVE_EXISTING_TARGETED_RUN')
env={k:v for k,v in os.environ.items() if not k.startswith('TCSC_')}
exe=R/'build/owner_controls_v1.exe'
started=time.monotonic();p=subprocess.run([str(exe),'--control-tests'],env=env,capture_output=True,timeout=30)
(R/'audit/targeted.stdout.jsonl').write_bytes(p.stdout);(R/'audit/targeted.stderr.log').write_bytes(p.stderr)
if p.returncode:raise RuntimeError('TARGETED_TEST_FAILED_NO_AUTOMATIC_RETRY')
rows=[json.loads(line) for line in p.stdout.splitlines()];summary=rows[-1]
assert summary['status']=='CPU_TARGETED_PASS' and summary['full_arrays']==32
assert summary['driver_loaded'] is False and summary['GPU_launches']==0
# The CLI performs three CPU reference/replay checks, then rejects before
# native::init. No old or new execution-permit variable is activated.
gate=subprocess.run([str(exe),'--execute',str(R.parent/'fixtures/gpu_micro7.edges'),'7','7','3'],env=env,capture_output=True,timeout=15)
(R/'audit/gate.stdout.log').write_bytes(gate.stdout);(R/'audit/gate.stderr.log').write_bytes(gate.stderr)
assert gate.returncode==2 and b'HOLD_ENVIRONMENT' in gate.stderr and b'driver_loaded=0 kernels=0' in gate.stderr
result={'status':'CPU_TARGETED_AND_PRE_DRIVER_GATE_PASS','targeted':summary,
 'targeted_graphs':8,'new_control_distance_arrays':32,'CLI_pre_driver_CPU_arrays':3,
 'pre_driver_gate_rejections':1,'GPU_queries':0,'GPU_execution':0,'old_402_suite_repeated':False,
 'sanitizer_runs':0,'seconds_for_execution_audit_only':time.monotonic()-started,
 'GPU_correctness':'UNMEASURED','GPU_performance':'UNMEASURED'}
(R/'audit/CPU_TARGETED_RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
