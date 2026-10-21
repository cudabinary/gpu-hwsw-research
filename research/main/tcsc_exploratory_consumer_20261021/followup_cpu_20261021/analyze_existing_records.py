"""Arithmetic on six preserved timing logs only. No subprocess or GPU API."""
from pathlib import Path
import csv,hashlib,json
D=Path(__file__).resolve().parent;P=D.parent;RAW=P/'results/EXPLORATORY_SESSION'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(path,rows):
    with path.open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def main():
    O=D/'calculations';O.mkdir(exist_ok=False)
    receipt=json.loads((RAW/'RECEIPT.json').read_text());plan=json.loads((P/'config/PLAN.json').read_text())
    inputs={};requests=[];prefixes=[];setup=[];per_worker={}
    for item in receipt['completed']:
        if item['case']['phase']!='EXPLORATORY_TIMING':continue
        worker=item['index'];case=item['case'];path=RAW/f'{worker:02d}.stdout.log';inputs[path.relative_to(P).as_posix()]=sha(path)
        lines=[json.loads(x) for x in path.read_text().splitlines() if x.startswith('{')]
        bfs=[x for x in lines if x['kind']=='BFS'];batch=next(x for x in lines if x['kind']=='BATCH')
        assert len(bfs)==32 and bfs==[x for x in item['results'] if x['kind']=='BFS']
        previous=0.0;rows=[]
        for x in bfs:
            increment=x['owned_ready_prefix_ms']-previous;previous=x['owned_ready_prefix_ms']
            row={'worker':worker,'block':case['block'],'mode':case['mode'],'query':x['query'],'source':x['source'],
              'delivered_increment_ms':increment,'query_wall_ms':x['wall_ms'],'owned_ready_prefix_ms':x['owned_ready_prefix_ms'],
              'stream_event_interval_ms_not_busy_time':x['stream_interval_ms'],
              'host_output_allocation_plus_D2H_ms':x['return_copy_ms'],
              'wrapper_increment_minus_query_wall_ms':increment-x['wall_ms'],
              'levels':x['levels'],'kernel_launches':x['kernel_launches'],'seen':x['seen'],
              'reason':x['reason'],'reconstructed_edge_tests_not_GPU_traffic':x['reconstructed_edge_tests']}
            requests.append(row);rows.append(row)
        per_worker[(case['block'],case['mode'])]=rows
        setup.append({'worker':worker,'block':case['block'],'mode':case['mode'],
          **{k:batch[k] for k in ['graph_load_ms','cpu_reverse_build_ms','cpu_reference_and_work_replay_ms',
            'context_setup_transfer_ms','static_bound_setup_ms','batch_ms','post_batch_validation_ms','device_payload_bytes']},
          'worker_wall_upper_bound_seconds':item['worker_wall_upper_bound_seconds'],
          'GPU_reverse_build_ms':'UNKNOWN_NOT_RUN','H2D_only_ms':'UNKNOWN_COMPOSITE_SETUP',
          'allocation_only_ms':'UNKNOWN_COMPOSITE_SETUP_OR_QUERY','GPU_kernel_busy_ms':'UNKNOWN_HOST_GAPS_IN_EVENTS'})
        for q in [1,2,8,32]:
            selected=rows[:q]
            prefixes.append({'block':case['block'],'mode':case['mode'],'q':q,'owned_complete_ms':selected[-1]['owned_ready_prefix_ms'],
              'mean_delivered_increment_ms_descriptive':selected[-1]['owned_ready_prefix_ms']/q,
              'sum_query_wall_ms':sum(x['query_wall_ms'] for x in selected),
              'sum_stream_intervals_ms_not_busy_time':sum(x['stream_event_interval_ms_not_busy_time'] for x in selected),
              'sum_output_allocation_plus_D2H_ms':sum(x['host_output_allocation_plus_D2H_ms'] for x in selected),
              'largest_increment_query':max(selected,key=lambda x:x['delivered_increment_ms'])['query'],
              'largest_increment_ms':max(x['delivered_increment_ms'] for x in selected),
              'rows_are_nested_prefixes_not_independent_samples':True})
    changes=[];paired_requests=[];prefix_changes=[];paired_prefix=[]
    for mode in [7,8,5]:
        for a,b in zip(per_worker[(0,mode)],per_worker[(1,mode)]):
            assert a['source']==b['source'] and a['query']==b['query']
            changes.append({'mode':mode,'query':a['query'],'source':a['source'],
              'order_A_increment_ms':a['delivered_increment_ms'],'order_B_increment_ms':b['delivered_increment_ms'],
              'B_minus_A_increment_ms':b['delivered_increment_ms']-a['delivered_increment_ms'],
              'A_query_wall_ms':a['query_wall_ms'],'B_query_wall_ms':b['query_wall_ms'],
              'A_event_ms':a['stream_event_interval_ms_not_busy_time'],'B_event_ms':b['stream_event_interval_ms_not_busy_time'],
              'same_logical_work':all(a[k]==b[k] for k in ['levels','kernel_launches','seen','reconstructed_edge_tests_not_GPU_traffic']),
              'cause_of_order_difference':'UNKNOWN_NOT_IDENTIFIED'})
        for q in [1,2,8,32]:
            a=next(x for x in prefixes if x['block']==0 and x['mode']==mode and x['q']==q)
            b=next(x for x in prefixes if x['block']==1 and x['mode']==mode and x['q']==q)
            prefix_changes.append({'mode':mode,'q':q,'order_A_ms':a['owned_complete_ms'],'order_B_ms':b['owned_complete_ms'],
              'B_minus_A_ms':b['owned_complete_ms']-a['owned_complete_ms'],
              'B_over_A':b['owned_complete_ms']/a['owned_complete_ms'],
              'B_delta_percent':100*(b['owned_complete_ms']/a['owned_complete_ms']-1)})
    for block in [0,1]:
        for i in range(32):
            a=per_worker[(block,7)][i];b=per_worker[(block,8)][i];d=per_worker[(block,5)][i]
            paired_requests.append({'block':block,'query':i,'source':a['source'],'lean7_increment_ms':a['delivered_increment_ms'],
              'stats8_increment_ms':b['delivered_increment_ms'],'Direction5_increment_ms':d['delivered_increment_ms'],
              'Direction_minus_lean_ms':d['delivered_increment_ms']-a['delivered_increment_ms'],
              'Direction_minus_stats_ms':d['delivered_increment_ms']-b['delivered_increment_ms']})
        for q in [1,2,8,32]:
            bymode={x['mode']:x for x in prefixes if x['block']==block and x['q']==q}
            for control in [7,8]:
                d=bymode[5]['owned_complete_ms'];a=bymode[control]['owned_complete_ms']
                paired_prefix.append({'block':block,'q':q,'Push_control':control,'Direction5_ms':d,'Push_ms':a,
                  'Direction_minus_Push_ms':d-a,'Direction_over_Push':d/a,'delta_percent':100*(d/a-1)})
    write_csv(O/'request_timings_192.csv',requests);write_csv(O/'request_order_differences_96.csv',changes)
    write_csv(O/'same_source_mode_comparisons_64.csv',paired_requests)
    write_csv(O/'prefix_boundaries_24.csv',prefixes);write_csv(O/'prefix_order_differences_12.csv',prefix_changes)
    write_csv(O/'paired_prefix_comparisons_16.csv',paired_prefix);write_csv(O/'setup_boundaries_6.csv',setup)
    largest=[]
    for mode in [7,8,5]:
        selected=[x for x in changes if x['mode']==mode];total=sum(x['B_minus_A_increment_ms'] for x in selected)
        top=max(selected,key=lambda x:abs(x['B_minus_A_increment_ms']))
        largest.append({'mode':mode,'total_B_minus_A_ms':total,'largest_absolute_difference_query':top['query'],
          'source':top['source'],'largest_difference_ms':top['B_minus_A_increment_ms'],
          'other_31_queries_difference_ms':total-top['B_minus_A_increment_ms'],
          'no_request_removed':True,'cause':'UNKNOWN'})
    for rel in ['results/EXPLORATORY_SESSION/RECEIPT.json','config/PLAN.json','src/owner_controls_v1.cpp','src/native_driver.hpp']:
        inputs[rel]=sha(P/rel)
    strict=P.parent/'MAIN_TCSC_READY_CONSUMER_ROUND_20261021'
    assert all(sha(strict/rel)==digest for rel,digest in plan['strict_preservation_pins'].items())
    summary={'scope':'BOUNDED_CPU_ARITHMETIC_ON_EXISTING_RECORDS','new_GPU_queries_or_runs':0,'new_BFS_or_correctness_runs':0,
      'timing_workers_read':6,'requests_read':192,'separate_measurement_sessions':1,'order_blocks':2,
      'confidence_intervals':'NOT_COMPUTED_INSUFFICIENT_SESSION_REPLICATION','causal_order_effect':'UNKNOWN',
      'all_96_same_source_mode_order_work_checks_equal':all(x['same_logical_work'] for x in changes),
      'largest_order_differences_retained':largest,'sequential_vs_concurrent_preparation_total_cost':'UNKNOWN_NOT_MEASURED',
      'strongest_lean_question':'Does ready Direction reproduce a q32 advantage over mode7 while reporting its q1/q2/q8 cost?',
      'strict_and_raw_inputs_preserved':True,'input_sha256':inputs}
    (O/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({'order_differences_q32':[x for x in prefix_changes if x['q']==32],'largest_differences':largest,'new_GPU_calls':0},indent=2))
if __name__=='__main__':main()
