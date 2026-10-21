"""Run exactly the two newly approved sessions, one 600-second wall budget."""
from pathlib import Path
from ctypes import wintypes as W
import argparse,ctypes,datetime as dt,hashlib,json,os,time,traceback
import session_runner
P=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2))
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--exploratory-isolation-unverified',action='store_true',required=True);parser.add_argument('--dry-plan',action='store_true');args=parser.parse_args()
    plan=json.loads((P/'config/PLAN.json').read_text())
    assert plan['explicit_user_authorized'] and plan['contract']=='ISOLATION_UNVERIFIED'
    assert plan['session_order']==['S2','S3'] and plan['campaign_wall_cap_seconds']==600
    cases=[c for name in plan['session_order'] for c in plan['sessions'][name]['cases']]
    assert len(cases)==12 and sum(c['q'] for c in cases)==268 and sum(c['q']==3 for c in cases)==4
    assert all(c['mode'] in (5,7) for c in cases)
    assert sha(P/'config/PLAN.json')==(P/'audit/PLAN_SHA256.txt').read_text().split()[0]
    for rel,digest in plan['pins'].items():assert sha(P/rel)==digest,rel
    old=P.parent/'MAIN_TCSC_EXPLORATORY_CONSUMER_20261021'
    for rel,digest in plan['prior_round_preservation'].items():assert sha(old/rel)==digest,rel
    if args.dry_plan:print(json.dumps({'status':'CPU_DRY_PLAN_PASS','CUDA_workers_max':12,'BFS_max':268,'init_cancels_max':4,'GPU_queries':0}));return
    R=P/'results/CAMPAIGN';R.mkdir(exist_ok=False)
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE];k.CreateFileW.restype=W.HANDLE;k.CloseHandle.argtypes=[W.HANDLE]
    handle=k.CreateFileW(str(R/'CAMPAIGN.lock'),0xC0000000,0,None,4,0x80,None)
    if handle==ctypes.c_void_p(-1).value:raise RuntimeError('CAMPAIGN_LOCK_UNAVAILABLE')
    start=time.monotonic();deadline=start+600;completed=[]
    save(R/'START.json',{'started_utc':utc(),'contract':'ISOLATION_UNVERIFIED','wall_cap_seconds':600,'plan_sha256':sha(P/'config/PLAN.json'),'worker_cap':12,'BFS_cap':268,'cancel_cap':4})
    try:
        for name in plan['session_order']:
            if time.monotonic()+30>deadline:raise RuntimeError('CAMPAIGN_DEADLINE_BEFORE_SESSION')
            session_runner.run_session(name,deadline)
            receipt=json.loads((P/'results'/name/'RECEIPT.json').read_text())
            preserved=json.loads((P/'results'/name/'STRICT_PRESERVATION_CHECK.json').read_text())
            if receipt['processes']!=6 or receipt['BFS']!=134 or receipt['init_only_cancellations']!=2:raise RuntimeError('SESSION_SCOPE_MISMATCH')
            if not preserved['all_preserved'] or receipt['context_end']!='CONTEXT_RELEASE_MARKER_AND_PID_ABSENCE_CONFIRMED':raise RuntimeError('RETIREMENT_OR_PRESERVATION_FAILURE')
            completed.append({'session':name,'receipt_sha256':sha(P/'results'/name/'RECEIPT.json'),'workers':6,'BFS':134,'init_only_cancellations':2})
            if name=='S2':
                until=time.monotonic()+60
                if until+30>deadline:raise RuntimeError('INSUFFICIENT_BUDGET_FOR_GAP_AND_S3')
                save(R/'GAP_START.json',{'utc':utc(),'duration_seconds':60,'GPU_dispatch_during_gap':0})
                print('S2_COMPLETE_BEGIN_60_SECOND_NO_GPU_DISPATCH_GAP',flush=True)
                while True:
                    remaining=until-time.monotonic()
                    if remaining<=0:break
                    time.sleep(min(5,remaining))
                save(R/'GAP_END.json',{'utc':utc(),'elapsed_campaign_seconds':time.monotonic()-start})
        if time.monotonic()>deadline:raise RuntimeError('CAMPAIGN_WALL_CAP')
        total=sum(f.stat().st_size for f in (P/'results').rglob('*') if f.is_file())
        if total>128<<20:raise RuntimeError('CAMPAIGN_RAW_STORAGE_CAP')
        save(R/'RECEIPT.json',{'status':'APPROVED_TWO_SESSIONS_PASS','completed_utc':utc(),'contract':'ISOLATION_UNVERIFIED','whole_campaign_wall_seconds_including_gap':time.monotonic()-start,
          'CUDA_workers':12,'GPU_BFS_arrays':268,'init_only_cancellations':4,'sessions':completed,'raw_result_bytes':total,'automatic_retries':0,'scope_expanded':False})
        print('CAMPAIGN_PASS_12_WORKERS_268_BFS_4_INIT_CANCEL',flush=True)
    except BaseException as exc:
        save(R/'STOP.json',{'status':'STOPPED_NO_RETRY','reason':str(exc),'completed_sessions':completed,'wall_seconds':time.monotonic()-start,'traceback':traceback.format_exc()})
        raise
    finally:
        k.CloseHandle(handle)
        save(R/'PRIOR_ROUND_PRESERVATION.json',{'unchanged':{rel:sha(old/rel)==digest for rel,digest in plan['prior_round_preservation'].items()},'old_results_modified':False})
if __name__=='__main__':main()
