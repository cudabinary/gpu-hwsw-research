"""Write a non-executable approval proposal and exact source-boundary anchors."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;P=D.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if (D/'PROPOSED_GPU_PLAN.json').exists():raise RuntimeError('PRESERVE_EXISTING_PROPOSAL')
    anchors={'src/owner_controls_v1.cpp':[
      'auto load_start','auto build_start','auto reference_start','auto setup_start',
      'cudaMemcpy(row,g_->row()','cudaMemcpy(row,r_->row()','auto bound_start',
      'Answer query(','require(!failed_','reader identity','auto start=Clock::now()',
      'native::launch("r_init"','cudaMemsetAsync(d_.counter','cudaMemsetAsync(d_.bitmap',
      'Counter c{}','std::swap(d_.front','cudaEventRecord(end','auto out=std::make_shared',
      'a.distance=out','auto batch_start','auto validation_start','std::ofstream output','owner.close()'],
      'src/native_driver.hpp':['cuModuleLoadData','static std::map<std::string,CUfunction>','cuModuleGetFunction']}
    mapping=[]
    for rel,patterns in anchors.items():
        lines=(P/rel).read_text().splitlines()
        for term in patterns:
            hits=[{'line':i,'text':line.strip()} for i,line in enumerate(lines,1) if term in line]
            assert hits,(rel,term)
            mapping.append({'path':rel,'sha256':sha(P/rel),'pattern':term,'matches':hits})
    (D/'TIMING_BOUNDARIES.json').write_text(json.dumps({'scope':'SOURCE_READING_ONLY','anchors':mapping,'GPU_queries':0},indent=2))
    sourceplan=json.loads((P/'config/PLAN.json').read_text());sessions=[]
    for name,smoke,orders in [('S2',[5,7],[[5,7],[7,5]]),('S3',[7,5],[[7,5],[5,7]])]:
        cases=[{'phase':'SMOKE','fixture':'gpu_micro7.edges','n':7,'mode':mode,'q':3} for mode in smoke]
        for block,order in enumerate(orders):cases.extend({'phase':'TIMING','fixture':'livejournal_sampled_4096.edges','n':4096,'mode':mode,'q':32,'block':block} for mode in order)
        sessions.append({'name':name,'cases':cases,'worker_cap':6,'session_wall_cap_seconds':180,'maximum_management_observations':1200})
    workers=sum(len(x['cases']) for x in sessions);arrays=sum(c['q'] for x in sessions for c in x['cases']);cancels=sum(c['q']==3 for x in sessions for c in x['cases'])
    assert (workers,arrays,cancels)==(12,268,4)
    proposal={'status':'PROPOSED_NOT_APPROVED_NOT_EXECUTED','execution_authorized':False,'dispatch_ready':False,
      'question':'Reproducibility of ready Direction5 versus strongest tested lean Push7 q32, with all short-prefix costs retained',
      'sessions':sessions,'NEW_CUDA_workers_max':workers,'NEW_BFS_arrays_max':arrays,'NEW_init_only_cancellations_max':cancels,
      'NEW_total_query_calls_max':arrays+cancels,'completed_old_session_reclassified_as_new':False,
      'separation_no_research_GPU_dispatch_seconds':60,'whole_enabled_session_wall_cap_seconds':360,'child_wall_window_cap_seconds':240,
      'estimated_enabled_wall_seconds':[16,50],'estimated_wall_including_spacing_seconds':[76,110],
      'estimates_are_unmeasured':True,'minimum_free_start_MiB':2048,'minimum_free_run_MiB':1536,
      'temperature_exclusive_limit_C':78,'workspace_request_cap_bytes':33554432,'observed_old_LJ_device_payload_bytes':501580,
      'extra_driver_context_background_bytes':'UNKNOWN','child_watchdog_seconds':20,'telemetry_freshness_ms':3000,
      'warmup':0,'automatic_retries':0,'Nsight_Systems_processes':0,'Nsight_Compute_processes':0,'sanitizer_processes':0,
      'new_kernels_or_datasets':False,'new_compilation_planned':False,
      'measurement_contract':'MUST_BE_REAPPROVED; exploratory implies ISOLATION_UNVERIFIED, not strict isolation',
      'external_CUDA_absence_and_WSL_coverage':'UNKNOWN unless a newly validated observation contract establishes more',
      'existing_pins':{k:v for k,v in sourceplan['pins'].items() if k.startswith(('build/','src/','include/','fixtures/'))},
      'q_prefixes':[1,2,8,32],'sources':[17*i for i in range(32)],
      'primary_ratio':'Direction5 owned q32 prefix / Push7 owned q32 prefix, within each block',
      'confidence_intervals':'NONE_PLANNED_INSUFFICIENT_REPLICATION_FOR_FINAL_CLAIMS',
      'interpretation':'All four prospective ratios <0.95 is a consistent exploratory signal for review only; retain two historical ratios separately including adverse result. Any prospective sign reversal remains unresolved. No selection or adaptive extra runs.',
      'automatic_builder_concurrency_or_HW_expansion':False,'GPU_queries_or_execution_by_this_followup':0}
    (D/'PROPOSED_GPU_PLAN.json').write_text(json.dumps(proposal,indent=2))
    files=[p for p in D.rglob('*') if p.is_file() and p.name!='SHA256SUMS']
    (D/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(D).as_posix()+'\n' for p in sorted(files)))
    print(json.dumps({'followup':'CPU_ONLY_COMPLETE','new_GPU_calls':0,'proposed_workers_only':workers,'proposed_arrays_only':arrays,'proposed_cancels_only':cancels,'files':len(files)+1}))
if __name__=='__main__':main()
