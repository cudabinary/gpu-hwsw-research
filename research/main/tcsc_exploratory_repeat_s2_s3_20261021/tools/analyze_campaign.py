"""Offline analysis of the frozen S2/S3 campaign, retaining original S1."""
from pathlib import Path
import csv,hashlib,json,re,shutil
P=Path(__file__).resolve().parents[1];OLD=P.parent/'MAIN_TCSC_EXPLORATORY_CONSUMER_20261021'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def csv_write(path,rows):
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    O=P/'results/analysis_complete';O.mkdir(exist_ok=False)
    historical=P/'historical/S1';historical.mkdir(parents=True,exist_ok=True)
    for rel in ['RECEIPT.json']+[f'{i:02d}.stdout.log' for i in range(3,9)]:
        dest=historical/rel
        if not dest.exists():shutil.copyfile(OLD/'results/EXPLORATORY_SESSION'/rel,dest)
        else:assert sha(dest)==sha(OLD/'results/EXPLORATORY_SESSION'/rel)
    (historical/'REFERENCE.json').write_text(json.dumps({'scope':'Previously completed S1; never recounted as NEW execution',
      'original_result_commit':'172aec74f0e3866eefb3811b2b61163ac946c2f4','CPU_followup_commit':'0d6562842edd04c15af1ce61fc5ed058cbe53a47',
      'Library_file_id':'libfile_34333c84fc2c81918109b62a3db225f2','Library_version':1,
      'Library_version_file_id':'file_0000000077b48211b05e5e8837feadff','original_ZIP_SHA256':'936f275015902b2a3d09ed27d7e9b52f1a5769e2fc2ae1ce04911d07a771f3c7'},indent=2))
    campaign=json.loads((P/'results/CAMPAIGN/RECEIPT.json').read_text());assert campaign['GPU_BFS_arrays']==268
    rows=[];workers=[];prefixes=[];pairings=[];sessions=[];total_submissions=0;new_queries=[]
    for name in ['S1','S2','S3']:
        R=historical if name=='S1' else P/'results'/name
        receipt=json.loads((R/'RECEIPT.json').read_text())
        if name!='S1':
            telemetry=json.loads((R/'TELEMETRY.json').read_text())
            sessions.append({'session':name,'workers':receipt['processes'],'BFS':receipt['BFS'],'init_cancels':receipt['init_only_cancellations'],
              'session_wall_to_context_release_seconds':receipt['whole_session_seconds'],'CUDA_worker_wall_upper_bound_seconds':receipt['CUDA_worker_wall_upper_bound_seconds'],
              'Python_reference_preparation_seconds':receipt['Python_reference_preparation_seconds'],
              'telemetry_samples':len(telemetry),'max_temperature_C':max(x['temperature_C'] for x in telemetry),'min_free_MiB':min(x['free_MiB'] for x in telemetry),
              'initial_context_entries':len(telemetry[0]['processes']),'unreadable_names':sum(not x['name'] or 'Insufficient' in x['name'] for x in telemetry[0]['processes']),
              'contract':'ISOLATION_UNVERIFIED','context_end':receipt['context_end']})
        for item in receipt['completed']:
            c=item['case'];bfs=[x for x in item['results'] if x['kind']=='BFS'];batch=next(x for x in item['results'] if x['kind']=='BATCH')
            if name!='S1':
                marker=re.search(r'CONTEXT_RELEASED_SYNC_OK kernels=(\d+)',(R/f"{item['index']:02d}.stderr.log").read_text());assert marker
                submitted=int(marker[1]);assert submitted==sum(x['kernel_launches'] for x in bfs)+batch['cancel_tests'];total_submissions+=submitted;new_queries+=bfs
                workers.append({'session':name,'worker':item['index'],**c,'block':c.get('block',-1),**batch,'worker_window_seconds':item['worker_wall_upper_bound_seconds'],'actual_kernel_launch_submissions_including_cancel':submitted})
            if c['phase']!='EXPLORATORY_TIMING':continue
            previous=0
            for x in bfs:
                rows.append({'session':name,'new_execution':name!='S1','worker':item['index'],'block':c['block'],'mode':c['mode'],
                  'query':x['query'],'source':x['source'],'delivered_increment_ms':x['owned_ready_prefix_ms']-previous,**x})
                previous=x['owned_ready_prefix_ms']
            for q in [1,2,8,32]:
                prefixes.append({'session':name,'new_execution':name!='S1','block':c['block'],'mode':c['mode'],'q':q,
                  'owned_ready_prefix_ms':bfs[q-1]['owned_ready_prefix_ms'],
                  'event_interval_sum_ms_not_busy_time':sum(x['stream_interval_ms'] for x in bfs[:q]),
                  'output_allocation_and_D2H_sum_ms':sum(x['return_copy_ms'] for x in bfs[:q]),
                  'actual_launch_submissions':sum(x['kernel_launches'] for x in bfs[:q]),
                  'reconstructed_edge_tests_not_GPU_traffic':sum(x['reconstructed_edge_tests'] for x in bfs[:q])})
    for session in ['S1','S2','S3']:
        for block in [0,1]:
            for q in [1,2,8,32]:
                modes={x['mode']:x for x in prefixes if x['session']==session and x['block']==block and x['q']==q}
                ratio=modes[5]['owned_ready_prefix_ms']/modes[7]['owned_ready_prefix_ms']
                pairings.append({'session':session,'new_execution':session!='S1','block':block,'q':q,
                  'lean_Push7_ms':modes[7]['owned_ready_prefix_ms'],'Direction5_ms':modes[5]['owned_ready_prefix_ms'],
                  'Direction_over_lean':ratio,'Direction_delta_percent':100*(ratio-1),'contract':'ISOLATION_UNVERIFIED'})
    csv_write(O/'request_raw_including_historical.csv',rows);csv_write(O/'new_worker_raw.csv',workers)
    csv_write(O/'prefixes_including_historical.csv',prefixes);csv_write(O/'paired_ratios.csv',pairings);csv_write(O/'new_session_resources.csv',sessions)
    q32=[x for x in pairings if x['q']==32];newq=[x for x in q32 if x['new_execution']]
    assert len(newq)==4 and len(new_queries)==268
    consistent=all(x['Direction_over_lean']<0.95 for x in newq)
    plan=json.loads((P/'config/PLAN.json').read_text())
    preserved=all(sha(P/rel)==digest for rel,digest in plan['pins'].items())
    preserved&=all(sha(OLD/rel)==digest for rel,digest in plan['prior_round_preservation'].items())
    assert preserved
    summary={'status':'CONSISTENT_PROSPECTIVE_EXPLORATORY_SIGNAL' if consistent else 'PROSPECTIVE_UTILITY_UNRESOLVED',
      'contract':'ISOLATION_UNVERIFIED','new_CUDA_workers':12,'new_full_BFS_arrays_checked':268,'Cplusplus_full_array_checks':268,'Python_full_array_checks':268,
      'new_init_only_cancellations':4,'actual_new_kernel_launch_submissions_including_cancel':total_submissions,
      'correctness_or_CUDA_errors':0,'watchdog_or_observed_environment_stops':0,'automatic_retries':0,
      'whole_campaign_wall_seconds_including_gap':campaign['whole_campaign_wall_seconds_including_gap'],
      'CUDA_worker_wall_window_sum_seconds':sum(x['CUDA_worker_wall_upper_bound_seconds'] for x in sessions),
      'query_stream_event_interval_sum_ms_not_GPU_busy_time':sum(x['stream_interval_ms'] for x in new_queries),
      'CPU_reverse_build_ms_sum':sum(x['cpu_reverse_build_ms'] for x in workers),
      'Python_reference_CPU_preparation_seconds_sum':sum(x['Python_reference_preparation_seconds'] for x in sessions),
      'max_observed_temperature_C':max(x['max_temperature_C'] for x in sessions),'min_observed_free_MiB':min(x['min_free_MiB'] for x in sessions),
      'telemetry_samples':sum(x['telemetry_samples'] for x in sessions),'raw_result_bytes_at_campaign_receipt':campaign['raw_result_bytes'],
      'all_owned_contexts_released_and_PIDs_absent':True,'original_sources_and_results_preserved':preserved,
      'new_q32_ratios':newq,'historical_q32_ratios_retained':[x for x in q32 if not x['new_execution']],
      'prospective_four_pair_margin_passed':consistent,'historical_adverse_order_erased':False,
      'external_CUDA_absence':'UNKNOWN','WSL_context_coverage':'UNKNOWN','enforced_isolation':False,
      'stable_or_general_performance_proof':False,'confidence_intervals':'NOT_COMPUTED',
      'CPU_reverse_setup_H2D_costs_in_q_prefix':False,'GPU_builder_or_D0_D3_executed':False,
      'preparation_inclusive_service_advantage':'UNKNOWN','HW_causal_contribution':'UNESTABLISHED',
      'unexplained_cross_session_Direction_speed_change':'UNKNOWN_CAUSE; binary, inputs and logical trajectories are unchanged. Orchestration and unobserved environment can differ.',
      'next_action':'Review the consistent ready-consumer signal and unresolved regime difference before any separate preparation-inclusive plan; no automatic further GPU dispatch.'}
    (O/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
    (P/'audit/POSTSESSION_PIN_CHECK.json').write_text(json.dumps({'all_new_execution_pins_unchanged':preserved,'prior_round_preserved':True,'new_GPU_queries_for_check':0},indent=2))
    table=['| Session / block | Push7 q1 /q2 /q8 /q32 ms | Direction5 q1 /q2 /q8 /q32 ms | q32 D/P |','|---|---|---|---:|']
    for session in ['S1','S2','S3']:
        for block in [0,1]:
            cells=[]
            for mode in [7,5]:cells.append(' / '.join(format(next(x['owned_ready_prefix_ms'] for x in prefixes if x['session']==session and x['block']==block and x['mode']==mode and x['q']==q),'.4f') for q in [1,2,8,32]))
            ratio=next(x['Direction_over_lean'] for x in q32 if x['session']==session and x['block']==block)
            table.append('| '+session+'/'+str(block)+' | '+' | '.join(cells)+' | '+format(ratio,'.5f')+' |')
    report='''# Approved S2/S3 exploratory repeat: result

Exactly the two newly approved local RTX4060Ti sessions completed. No third
session, new input, tuning, kernel, build, profiler, sanitizer, installation,
paid resource, source deletion or OS/security/clock change was performed.
The measurement contract remains ISOLATION_UNVERIFIED; strict mode and the
earlier blocked capture remain unchanged. All source/binary/input pins match.

## Actual execution

Twelve CUDA workers completed268 BFS requests, each full distance array checked
by C++ and independent Python. These are268 requests checked twice, not536.
Four init-only cancellation checks published no output. Kernel submissions
including these cancellations: '''+str(total_submissions)+'''. No CUDA error, OOM, full-output mismatch,
watchdog or observed-environment stop occurred. Every worker reported synchronized
context release, exited and disappeared from the subsequent driver PID list.
This does not certify mid-kernel cancellation, sanitizer safety, injected queue
overflow or graph-mutation handling; it is the existing consumer-owner contract.

S2 smoke was[5,7], then timing[5,7]/[7,5]. S3 smoke was[7,5], then timing[7,5]/[5,7].
Smoke q3 sources were0/1/4; timing q32 sources were17*i, i=0..31, unchanged.
The60-second no-dispatch gap followed S2 retirement/helper cleanup. Whole
campaign wall including the gap and session cleanup was '''+format(summary['whole_campaign_wall_seconds_including_gap'],'.3f')+''' seconds (<600).
New worker windows sum to '''+format(summary['CUDA_worker_wall_window_sum_seconds'],'.3f')+''' seconds; these include host/setup/waiting,
not GPU busy time. Query stream-event intervals sum to '''+format(summary['query_stream_event_interval_sum_ms_not_GPU_busy_time'],'.3f')+''' ms and contain
host gaps. CPU reverse builds sum to '''+format(summary['CPU_reverse_build_ms_sum'],'.4f')+''' ms; independent Python reference
preparation sums to '''+format(summary['Python_reference_CPU_preparation_seconds_sum'],'.3f')+''' CPU seconds. None is substituted for GPU conversion.

Across '''+str(summary['telemetry_samples'])+''' management snapshots, peak observed temperature was '''+str(summary['max_observed_temperature_C'])+''' C and
minimum free VRAM was '''+str(summary['min_observed_free_MiB'])+''' MiB. These are sampled extrema, not continuous guarantees.
LJ device payload remained501,580 bytes (32 MiB request cap). Driver/context
and background allocation is additional. Raw result bytes recorded at campaign
completion: '''+str(campaign['raw_result_bytes'])+''' (<128 MiB); derived reports are separate.

## Every order retained

'''+ '\n'.join(table)+'''

All four prospective q32 Direction/Push7 ratios are below the predeclared0.95
exploratory margin. New q1/q2/q8 prefixes also favor Direction in all four pairs.
This is a consistent prospective signal on this one input/contract. The old
S1 negative order and its short-prefix losses remain visible above; they were
not trimmed, replaced or reclassified. S1 mode8 records remain preserved but
were not rerun under this approval. No dominance over mode8 in the new sessions
or over a public strongest GPU BFS implementation is established.

There was no algorithm/binary/input change that explains the large Direction
time change from S1 to S2/S3. Logical level/kernel/work trajectories match the
frozen contract. New orchestration adds quota and campaign-deadline checks;
graphics/host scheduling, clocks, caches and other unobserved contention can
also differ. The reason is UNKNOWN. The new consistent pairs are not a proof
that the old adverse result was invalid. Do not pool these different regimes
into a confidence interval or claim final stable/general performance.

## Boundary and limits

Timing is ready-resident consumption, not whole preparation/service. CPU graph
load/reverse construction and native setup/H2D precede the query batch and are
recorded separately. Native setup also includes context/ACK/allocation costs;
it is not pure transfer time. Query distance initialization, events, counter/
bitmap initialization, level sync/control copies/free-memory safety checks,
host output allocation, full D2H and owned publication remain inside timing.
Validation and logging follow the batch. No safety check was disabled for speed.

External CUDA absence and WSL context visibility remain UNKNOWN. Initial C+G
background entries and unreadable names were not inspected via process memory
or modules. Low utilization/PID absence is not isolation proof. No hardware
counter or kernel timeline was collected. The experiment cannot attribute
memory/SM/control bottlenecks or our preparation method's causal contribution.

No GPU builder, Plan A/P joint-ready, D0-D3 or preparation-inclusive q-service
experiment ran. Those costs and HW necessity remain UNKNOWN/unestablished.
The new signal supplies a reason to REVIEW a separate full-cost question,
not permission to build/run it or change MAIN's research direction. This finite
approval is consumed. Stop and hand off the original evidence and all ratios.
'''
    (P/'reports/RESULT.md').write_text(report)
    print(json.dumps({'status':summary['status'],'q32_new':newq,'wall_s':summary['whole_campaign_wall_seconds_including_gap'],'temp_C':summary['max_observed_temperature_C'],'min_free_MiB':summary['min_observed_free_MiB'],'CPU_reverse_build_ms':summary['CPU_reverse_build_ms_sum']},indent=2))
if __name__=='__main__':main()
