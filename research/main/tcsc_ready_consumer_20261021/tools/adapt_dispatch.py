from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'input/archived_safety/roots/WIN_TASK/TCSC_RCC_RIE_CPU_STATIC_20261021/tools/gpu_pilot.py').read_text()
s=s.replace("P=Path(__file__).resolve().parents[1]","P=Path(__file__).resolve().parents[1]\nimport watchdog_support")
s=s.replace("config/GPU_MINIMAL_PILOT.json","config/ROUND_PLAN.json")
s=s.replace("plan['processes']==12 and plan['total_request_invocations']==48","plan['processes']==42 and plan['total_request_invocations']==1176")
s=s.replace("plan['dispatch_seconds']==300","plan['dispatch_seconds']==900")
s=s.replace("R=P/'results/GPU_PILOT'","R=P/'results/GPU_ROUND'")
s=s.replace("active=None;retired={}","active=None;retired={};watchdogs=[]")
s=s.replace("('engine','modules')","('engine','modules','wsl')")
s=s.replace("until=time.monotonic()+10", "guards.append(subprocess.Popen(['wsl.exe','-d','Ubuntu','--','python3','/mnt/c/'+(P/'tools/wsl_guard.py').as_posix()[3:],'--status','/mnt/c/'+(R/'wsl.status.json').as_posix()[3:],'--stop','/mnt/c/'+stop.as_posix()[3:]],creationflags=HIDDEN))\n        until=time.monotonic()+10")
s=s.replace("('engine','modules'))","('engine','modules','wsl'))")
s=s.replace("read(P/'results/gpu_abi_linux.stdout.log')","read(P/'audit/CPU_PREFLIGHT.json')['abi']")
s=s.replace("time.monotonic()-start+20>300","time.monotonic()-start+30>900")
s=s.replace("str(c['mode'])]+list(map(str,c['sources']))","str(c['mode']),str(c['q'])]")
begin=s.index('            cpu=subprocess.run(')
end=s.index("            ready=R/",begin)
s=s[:begin]+s[end:]
s=s.replace("CUDA_CACHE_DISABLE='1')","CUDA_CACHE_DISABLE='1',TCSC_DISTANCE_OUT=str(R/f'{i:02d}.distance.bin'))")
s=s.replace("began=time.monotonic();reason=[]","began=time.monotonic();reason=[];deadline_tick=watchdog_support.now_tick()+20000")
needle="child=active;launched.append(dict(index=i,pid=child.pid))"
s=s.replace(needle,needle+"\n                wd_path=R/f'{i:02d}.watchdog.json';wd=watchdog_support.start(child,wd_path,deadline_tick);watchdogs.append(wd)")
s=s.replace("if time.monotonic()-start>300","if time.monotonic()-start>900")
s=s.replace("if ready.exists() and not acknowledged:","if wd.poll() is not None and (child.poll() is None or read(wd_path)['status']!='CHILD_EXITED'):raise RuntimeError('independent watchdog failure')\n                        if ready.exists() and not acknowledged and wd_path.exists() and read(wd_path)['status']=='WATCHING':")
s=s.replace("finally:timer.cancel()","finally:timer.cancel()\n                wd.wait(timeout=3)\n                if wd.returncode or read(wd_path)['status']!='CHILD_EXITED':raise RuntimeError('independent watchdog boundary')")
old="bfs=[x for x in rows if x['kind']=='BFS'];cancels=[x for x in rows if x['kind']=='cancel']\n            assert len(bfs)==3 and len(cancels)==1 and all(x['status']=='PASS' and x['device_payload_bytes']<=32<<20 for x in bfs)"
new="bfs=[x for x in rows if x['kind']=='BFS'];batches=[x for x in rows if x['kind']=='BATCH']\n            assert len(bfs)==c['q'] and len(batches)==1 and all(x['status']=='PASS' for x in rows)\n            assert batches[0]['cancel_tests']==int(c['q']==3) and batches[0]['device_payload_bytes']<=32<<20\n            assert (R/f'{i:02d}.distance.bin').stat().st_size==4*c['n']*c['q']"
assert old in s;s=s.replace(old,new)
s=s.replace("'/ 12'","'/ 42'")
s=s.replace("BFS=36,cancellations=12","BFS=sum(x['case']['q'] for x in completed),cancellations=6")
s=s.replace("save(R/'TELEMETRY.json',samples);stop.touch()","save(R/'TELEMETRY.json',samples);stop.touch()\n        for w in watchdogs:\n            try:w.wait(timeout=3)\n            except subprocess.TimeoutExpired:w.kill();w.wait(timeout=3)")
(R/'tools/run_gpu_round.py').write_text(s)
