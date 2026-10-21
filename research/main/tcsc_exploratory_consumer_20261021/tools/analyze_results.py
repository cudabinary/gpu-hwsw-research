"""Offline summary of the sole exploratory session; never queries a GPU."""
from pathlib import Path
import csv,hashlib,json,re
P=Path(__file__).resolve().parents[1];R=P/'results/EXPLORATORY_SESSION'
def csv_file(path,rows):
    with path.open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def main():
    out=P/'results/analysis';out.mkdir(exist_ok=False)
    receipt=json.loads((R/'RECEIPT.json').read_text());telemetry=json.loads((R/'TELEMETRY.json').read_text())
    queries=[];workers=[];prefixes=[];actual_launches=0
    for item in receipt['completed']:
        case=item['case'];bfs=[x for x in item['results'] if x['kind']=='BFS'];batch=next(x for x in item['results'] if x['kind']=='BATCH')
        marker=re.search(r'CONTEXT_RELEASED_SYNC_OK kernels=(\d+)',(R/f"{item['index']:02d}.stderr.log").read_text())
        assert marker;submitted=int(marker[1]);assert submitted==sum(x['kernel_launches'] for x in bfs)+batch['cancel_tests'];actual_launches+=submitted
        for x in bfs:queries.append({'worker':item['index'],'phase':case['phase'],'block':case['block'],**x})
        workers.append({'worker':item['index'],**case,**batch,'worker_wall_upper_bound_seconds':item['worker_wall_upper_bound_seconds'],'actual_launch_submissions_including_cancel':submitted,'full_array_Python_verification':item['Python_full_array_check']})
        if case['phase']=='EXPLORATORY_TIMING':
            for q in [1,2,8,32]:prefixes.append({'block':case['block'],'mode':case['mode'],'q_prefix':q,'owned_ready_prefix_ms':bfs[q-1]['owned_ready_prefix_ms'],'total_edge_tests_reconstructed':sum(x['reconstructed_edge_tests'] for x in bfs[:q]),'actual_launch_submissions':sum(x['kernel_launches'] for x in bfs[:q]),'contract':'ISOLATION_UNVERIFIED'})
    ratios=[]
    for block in [0,1]:
        for q in [1,2,8,32]:
            modes={x['mode']:x for x in prefixes if x['block']==block and x['q_prefix']==q}
            for control in [7,8]:
                ratio=modes[5]['owned_ready_prefix_ms']/modes[control]['owned_ready_prefix_ms']
                ratios.append({'block':block,'q_prefix':q,'Direction_mode':5,'Push_control_mode':control,'Direction_prefix_ms':modes[5]['owned_ready_prefix_ms'],'Push_prefix_ms':modes[control]['owned_ready_prefix_ms'],'Direction_over_Push':ratio,'Direction_delta_percent':100*(ratio-1),'classification':'EXPLORATORY_DESCRIPTIVE_NOT_SUCCESS_TEST'})
    csv_file(out/'query_raw.csv',queries);csv_file(out/'worker_raw.csv',workers);csv_file(out/'paired_prefix_raw.csv',prefixes);csv_file(out/'paired_ratios.csv',ratios)
    q32=[x for x in ratios if x['q_prefix']==32]
    summary={'status':'ACTUAL_GPU_CORRECTNESS_PASS_EXPLORATORY_TIMING_MIXED','contract':'ISOLATION_UNVERIFIED',
      'new_CUDA_workers':len(workers),'unique_full_GPU_BFS_arrays':len(queries),'Cplusplus_full_array_checks':len(queries),'independent_Python_full_array_checks':len(queries),
      'init_only_cancellations':sum(x['cancel_tests'] for x in workers),'actual_kernel_launch_submissions_including_cancel':actual_launches,
      'GPU_errors_or_correctness_failures':0,'watchdog_or_environment_stops':0,'retries':0,
      'whole_session_wall_seconds':receipt['whole_session_seconds'],'CUDA_worker_wall_upper_bound_seconds':receipt['CUDA_worker_wall_upper_bound_seconds'],
      'sum_reported_query_stream_event_intervals_ms':sum(x['stream_interval_ms'] for x in queries),'GPU_kernel_busy_time':'NOT_MEASURED; events contain host gaps',
      'Python_reference_CPU_preparation_seconds':receipt['Python_reference_preparation_seconds'],
      'CPU_reverse_build_ms_total_across_workers':sum(x['cpu_reverse_build_ms'] for x in workers),
      'telemetry_samples':len(telemetry),'observed_max_temperature_C':max(x['temperature_C'] for x in telemetry),
      'observed_min_free_MiB':min(x['free_MiB'] for x in telemetry),'observed_max_free_MiB':max(x['free_MiB'] for x in telemetry),
      'initial_background_contexts':len(telemetry[0]['processes']),'initial_context_type_counts':{kind:sum(x['type']==kind for x in telemetry[0]['processes']) for kind in {x['type'] for x in telemetry[0]['processes']}},
      'initial_unreadable_names':sum(not x['name'] or 'Insufficient' in x['name'] for x in telemetry[0]['processes']),
      'external_CUDA_absence':'UNKNOWN','WSL_context_visibility':'UNKNOWN','complete_isolation':False,
      'protected_process_module_memory_queries':0,'security_driver_clock_changes':0,'Nsight_or_sanitizer_runs':0,
      'context_end':receipt['context_end'],'strict_mode_preserved':json.loads((R/'STRICT_PRESERVATION_CHECK.json').read_text())['all_preserved'],
      'paired_q32':q32,'stronger_Push_comparison':'Mode5 faster than mode8 in both orders, but mode5/mode7 changes winner; no robust utility verdict',
      'next_decision':'Ready GPU execution is feasible on tested inputs; do not expand to builder/concurrency or claim HW residual. Jointly review one next bounded measurement contract.',
      'not_tested':['isolated performance','GPU builder','D0-D3 overlap','CUDA sanitizer','mid-kernel cancellation','injected queue overflow','graph mutation/generation invalidation on GPU','common RCC API GPU backend']}
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
    table=['| Mode | Order A q1 / q2 / q8 / q32 (ms) | Order B q1 / q2 / q8 / q32 (ms) |','|---|---|---|']
    for mode,label in [(7,'7 lean static-bound Push'),(8,'8 equal-stop stats-Push'),(5,'5 Direction+zero+RIE')]:
        values=[]
        for block in [0,1]:values.append(' / '.join(format(next(x['owned_ready_prefix_ms'] for x in prefixes if x['block']==block and x['mode']==mode and x['q_prefix']==q),'.4f') for q in [1,2,8,32]))
        table.append('| '+label+' | '+' | '.join(values)+' |')
    text='''# Actual GPU exploratory result -- ISOLATION_UNVERIFIED

The sole explicitly authorized exploratory session completed. This does not
change or erase the earlier strict HOLD_ENVIRONMENT result. The old module
guard and blocked capture are hash-verified unchanged. No protected-process
module/memory inspection, OS/security/driver/clock change, installation,
profiler, paid resource, extra dataset or automatic retry occurred.

## Execution and exact correctness

Nine CUDA workers completed: three micro7 smoke workers (modes7/8/5, sources
0/1/4) followed only after success by six LJ4096/48292 q32 workers in fixed
orders [7,8,5] then [5,8,7]. All201 complete distance arrays matched the C++
oracle and an independent Python byte comparison. These are201 unique GPU
results checked twice, not402 results. Three init-only cancellation checks
published no result. Each worker reported synchronized context release, exited,
and disappeared from the subsequent driver process list before another launch.

No CUDA error, observed discovery-capacity violation, watchdog or correctness
failure occurred. This is not an injected overflow test, race/sanitizer proof,
mid-kernel cancellation test or validation of the common RCC API GPU backend.
The immutable graph and repeated requests exercise the legacy experimental
owner; graph-mutation/generation rejection was not newly tested on GPU.

## Fixed descriptive timing

Same resident CSR/reverse, full distance initialization/return and owned output
boundary for every mode. q prefixes share one fixed batch; no online arrivals.
Validation/log/file output is outside the batch. The two orders are from one
non-isolated session, not independent sessions or a confidence interval.

'''+ '\n'.join(table)+'''

Direction/lean-Push q32 changes winner between orders. Direction beats the
statistics-maintaining Push at q32 in both, but that is insufficient to beat
both strengthened baselines. At q1/q2/q8 Direction is slower than lean Push in
both orders. Every observation, including the adverse order, is retained. No
threshold, source, repetition or outcome was selected after observing results.

The current GPU harness is executable and exact on these tested cases. Stable
ready-consumer utility remains unresolved. Preparation-method causality,
preparation-inclusive service benefit, public strongest-SW superiority and HW
need are not established. No D0-D3 experiment was started.

## Timing/resource boundaries

Session wall: '''+format(summary['whole_session_wall_seconds'],'.3f')+''' seconds.
The summed CUDA-worker wall windows were '''+format(summary['CUDA_worker_wall_upper_bound_seconds'],'.3f')+''' seconds, a conservative
GPU-usage window including host/setup/waiting, not GPU busy time. Reported query
stream-event intervals sum to '''+format(summary['sum_reported_query_stream_event_intervals_ms'],'.3f')+''' ms and contain host gaps; kernel busy time
was not measured. Python reference preparation was '''+format(summary['Python_reference_CPU_preparation_seconds'],'.3f')+''' CPU seconds. CPU reverse
build times total '''+format(summary['CPU_reverse_build_ms_total_across_workers'],'.4f')+''' ms across nine workers. Context/H2D/handshake setup is recorded
separately in worker_raw.csv. No CPU duration is substituted for GPU conversion.

Peak observed temperature was '''+str(summary['observed_max_temperature_C'])+''' C; minimum free VRAM was '''+str(summary['observed_min_free_MiB'])+''' MiB. These are37
sampled observations, not continuous extrema. Workspace payload was501,580 bytes
for LJ (32 MiB cap); driver/context/background memory is outside that payload.
The free-VRAM variation cannot be attributed solely to this worker.

There were32 initial C+G entries and two unreadable process names. They remain
unverified background, not an innocuous allowlist. Known research names, foreign
pure-compute contexts, positive foreign compute engines, new PIDs, required
telemetry failures and abrupt background3D changes would stop the session.
Sampling can miss short activity, graphics shares resources, and WSL coverage
is incomplete/UNKNOWN. Neither low utilization nor PID absence proves isolation.
Host scheduling, clocks, caching and unobserved contention remain uncontrolled.

## Next decision

The smoke/array gate is closed positively for these inputs and binaries. Stop
this finite session. Review the next bounded measurement contract jointly;
do not launch more to obtain a preferred outcome or proceed automatically to
builder/concurrency/HW experiments. The remaining utility question is whether
Direction reliably beats BOTH strengthened Push controls under an accepted
measurement contract. Timing here is exploratory only.
'''
    (P/'reports/EXPLORATORY_RESULT.md').write_text(text)
    print(json.dumps({'status':summary['status'],'kernel_submissions':actual_launches,'q32':q32},indent=2))
if __name__=='__main__':main()
