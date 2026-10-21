"""Offline derivatives of saved observations. Never invokes a GPU API."""
from pathlib import Path
import csv,hashlib,io,json,shutil
R=Path(__file__).resolve().parents[1]
OUT=R/'audit/native_nvml_readonly_20261021'
raw=json.loads((OUT/'RESULT.json').read_text())
nv=raw['commands'][0]['observation']
rows=list(csv.DictReader(io.StringIO(raw['commands'][1]['output_text'])))
rows=[{k.strip():v.strip() for k,v in row.items()} for row in rows]
summary={'scope':'OFFLINE_DERIVATIVE_OF_ONE_NATIVE_READ_ONLY_DIAGNOSTIC',
 'start_utc':raw['commands'][0]['started_utc'],'end_utc':raw['commands'][-1]['ended_utc'],
 'driver_version':nv['driver_version'],'nvml_version':nv['nvml_version'],
 'device_name':nv['device_name'],'driver_model':'WDDM',
 'NVML_count_return_code':nv['compute_count_result']['return_code'],
 'NVML_reported_entries':nv['compute_count_result']['required_entries'],
 'nvidia_smi_exit_codes':{x['label']:x['exit_code'] for x in raw['commands'][1:]},
 'nvidia_smi_rows':len(rows),
 'unreadable_names':sum(x['process_name']=='[Insufficient Permissions]' for x in rows),
 'memory_values_NA':sum(x['used_gpu_memory [MiB]']=='[N/A]' for x in rows),
 'raw_result_sha256':hashlib.sha256((OUT/'RESULT.json').read_bytes()).hexdigest(),
 'CUDA_attribution_and_coverage':'UNKNOWN','isolation_proved':False,'guard_modified':False,
 'GPU_benchmark_resumed':False,'CUDA_workers':0,'GPU_BFS':0}
assert summary['nvidia_smi_rows']==32 and summary['unreadable_names']==2 and summary['memory_values_NA']==32
(R/'audit/NATIVE_NVML_DIAGNOSTIC_SUMMARY.json').write_text(json.dumps(summary,indent=2))
old=R/'audit/READ_THIS_UPDATE_BEFORE_NATIVE_DIAGNOSTIC.md'
if not old.exists():shutil.copy2(R/'00_READ_THIS_UPDATE_FIRST.md',old)
(R/'00_READ_THIS_UPDATE_FIRST.md').write_text('''# Latest update: read-only diagnosis complete, no GPU measurement resumed

GPU measurement remains on hold: CUDA workers=0, new GPU BFS=0, timing UNKNOWN.
CPU replay passed 402 full arrays and four negative argument tests. CPU results
do not establish GPU correctness for this new host or static cubin.

The previous module guard failure is an observability gap, not proof of another
CUDA job or of a lock-to-denial cause. No repeated unlock request, denied module
query retry, permission change or guard relaxation was made.

After separate read-only authorization, installed native Windows NVML and
nvidia-smi responded. NVML's NULL-array count call returned Insufficient Size
(7), count 32. CLI returned 32 entries, two unreadable names, all memory N/A on
WDDM. Neither complete CUDA attribution nor measurement isolation is proved.
Read reports/NATIVE_NVML_READONLY_DIAGNOSTIC.md for evidence, official sources
and the proposed measurement contract. This proposal does not authorize dispatch.

One separately requested WFA source archive was restored from one 64 MiB pack
to a protected new folder, verified, and recorded under the MAIN single-writer
ledger. Read reports/WFA_MINIMAL_RESTORE_HANDOFF.md. No paper repo was changed.

Earlier reports, raw failed captures and the original ZIP/Library version are
preserved. reports/OBSERVABILITY_REVIEW.md is the earlier source/document-only
review, before the separately authorized native management observation.
''')
result=json.loads((R/'reports/RESULT_SUMMARY.json').read_text())
result['read_only_native_diagnostic']='audit/NATIVE_NVML_DIAGNOSTIC_SUMMARY.json'
result['measurement_isolation_proved']=False
result['benchmark_resume_allowed']=False
result['WFA_restore']='reports/WFA_MINIMAL_RESTORE_HANDOFF.md'
(R/'reports/RESULT_SUMMARY.json').write_text(json.dumps(result,indent=2))
print(json.dumps(summary))
