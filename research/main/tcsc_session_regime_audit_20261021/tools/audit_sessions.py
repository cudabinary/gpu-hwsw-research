"""Bounded filesystem-only capture/reaggregation of existing GPU session records.

Never imports a CUDA runner, invokes a child, queries a GPU, or benchmarks.
"""
from pathlib import Path
import argparse, ast, collections, csv, hashlib, json, math, shutil
import xml.etree.ElementTree as ET

P = Path(__file__).resolve().parents[1]
PROJECTS = {'S1': 'MAIN_TCSC_EXPLORATORY_CONSUMER_20261021',
            'S23': 'MAIN_TCSC_EXPLORATORY_REPEAT_S2_S3_20261021'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def csv_write(path, rows):
    with path.open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def capture(workspace):
    dest = P / 'inputs'
    assert not dest.exists(), 'Existing capsule must not be replaced'
    requested = []
    common = ['config/PLAN.json', 'build/owner_controls_v1.exe', 'build/rcc_kernels.cubin',
        'src/owner_controls_v1.cpp', 'src/kernels.cu', 'src/host_controls.hpp', 'src/abi.hpp',
        'src/native_driver.hpp', 'include/independent_builder.hpp',
        'fixtures/livejournal_sampled_4096.edges', 'fixtures/gpu_micro7.edges']
    for alias, project in PROJECTS.items():
        for rel in common:
            requested.append((project + '/' + rel, alias + '/' + rel))
    for rel in ['tools/run_exploratory.py', 'audit/PRIOR_HOST_COMPILE.json', 'audit/SOURCE_SNAPSHOT.json']:
        requested.append((PROJECTS['S1'] + '/' + rel, 'S1/' + rel))
    for rel in ['tools/session_runner.py', 'tools/run_campaign.py', 'audit/PREEXECUTION_FREEZE.json',
                'audit/RUNNER_SCOPE_DIFF.patch', 'results/CAMPAIGN/START.json',
                'results/CAMPAIGN/GAP_START.json', 'results/CAMPAIGN/GAP_END.json', 'results/CAMPAIGN/RECEIPT.json']:
        requested.append((PROJECTS['S23'] + '/' + rel, 'S23/' + rel))
    for name, source, count in [('S1', PROJECTS['S1'] + '/results/EXPLORATORY_SESSION', 9),
                                 ('S2', PROJECTS['S23'] + '/results/S2', 6),
                                 ('S3', PROJECTS['S23'] + '/results/S3', 6)]:
        for rel in ['RECEIPT.json', 'SESSION_START.json', 'TELEMETRY.json', 'EXPLORATORY_BACKGROUND.json',
                    'engine.raw.jsonl', 'engine.status.json', 'STRICT_PRESERVATION_CHECK.json']:
            requested.append((source + '/' + rel, name + '/raw/' + rel))
        for i in range(count):
            for suffix in ['stdout.log', 'stderr.log', 'command.json', 'watchdog.json', 'distances.bin']:
                rel = f'{i:02d}.' + suffix
                requested.append((source + '/' + rel, name + '/raw/' + rel))
        for file in sorted((workspace / source).glob('telemetry_*.xml')):
            requested.append((source + '/' + file.name, name + '/raw/' + file.name))
    manifest = []
    for source, target in requested:
        data = (workspace / source).read_bytes()
        out = dest / target
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('xb') as f:
            f.write(data)
        assert sha(data) == sha((workspace / source).read_bytes()) == sha(out.read_bytes())
        manifest.append({'path': target, 'original_workspace_relative_path': source,
                         'sha256': sha(data), 'bytes': len(data)})
    save(P / 'INPUT_MANIFEST.json', {'scope': 'Existing files only; no new measurements',
        'source_main_commit': 'dd8ee313e0a843e245c632c485194841fe3c63d1', 'files': manifest})
    print(json.dumps({'status': 'READ_ONLY_CAPTURE_HASH_MATCH', 'files': len(manifest),
                      'bytes': sum(x['bytes'] for x in manifest), 'GPU_queries_or_runs': 0}))

def normalized_argv(command, alias):
    project = PROJECTS['S1'] if alias == 'S1' else PROJECTS['S23']
    result = []
    for value in command:
        value = value.replace('\\', '/')
        marker = '/' + project + '/'
        result.append('<PROJECT>/' + value.split(marker, 1)[1] if marker in value else value)
    return result

def analyze(output):
    inventory = read(P / 'INPUT_MANIFEST.json')['files']
    for item in inventory:
        assert sha((P / 'inputs' / item['path']).read_bytes()) == item['sha256'], item['path']
    O = P / output
    O.mkdir(exist_ok=False)
    I = P / 'inputs'
    equivalence = []
    for rel in ['build/owner_controls_v1.exe', 'build/rcc_kernels.cubin', 'src/owner_controls_v1.cpp',
                'src/kernels.cu', 'src/host_controls.hpp', 'src/abi.hpp', 'src/native_driver.hpp',
                'include/independent_builder.hpp', 'fixtures/livejournal_sampled_4096.edges',
                'fixtures/gpu_micro7.edges']:
        a, b = sha((I / 'S1' / rel).read_bytes()), sha((I / 'S23' / rel).read_bytes())
        assert a == b, rel
        equivalence.append({'relative_file': rel, 'S1_SHA256': a, 'S23_SHA256': b, 'equal': True})
    csv_write(O / 'BYTE_EQUIVALENCE.csv', equivalence)
    compile_receipt = read(I / 'S1/audit/PRIOR_HOST_COMPILE.json')
    assert compile_receipt['binary_sha256'] == equivalence[0]['S1_SHA256']
    env_assignments = []
    for alias, rel in [('S1', 'tools/run_exploratory.py'), ('S23', 'tools/session_runner.py')]:
        text = (I / alias / rel).read_text()
        tree = ast.parse(text)
        update = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and isinstance(n.func.value, ast.Name) and n.func.value.id == 'env' and n.func.attr == 'update')
        values = {x.arg: ast.unparse(x.value) for x in update.keywords}
        env_assignments.append({'session_group': alias, 'explicit_child_assignments_from_source': values,
            'full_historical_inherited_environment': 'UNKNOWN_NOT_RECORDED', 'explicit_cwd': 'ABSENT_IN_POPEN; INHERITED_CWD_UNKNOWN'})
    assert env_assignments[0]['explicit_child_assignments_from_source'] == env_assignments[1]['explicit_child_assignments_from_source']
    save(O / 'ENVIRONMENT_AND_BUILD.json', {'environment': env_assignments,
        'host_compile_argv': normalized_argv(compile_receipt['argv'], 'S1'),
        'host_compile_exit': compile_receipt['exit_code'], 'host_build_output_matches_both_sessions': True,
        'compiler_version': 'UNKNOWN_NOT_RECORDED_IN_RECEIPT',
        'original_CUDA_compile_flags': 'UNKNOWN_IN_INSPECTED_SESSION_RECORDS; same existing cubin bytes',
        'new_compilations_in_S2_S3': False, 'warmup_declared_both': 0,
        'CUDA_CACHE_DISABLE_explicit_both': '1; recorded source assignment, no child environment echo',
        'device_cache_residency_or_flush': 'UNKNOWN_NOT_RECORDED',
        'driver_cache_and_clock_causes': 'UNKNOWN; no causal inference from current-state inspection'})
    workers, requests, telemetry, schedules, pairs = [], [], [], [], []
    lookup = {}
    for name in ['S1', 'S2', 'S3']:
        R = I / name / 'raw'
        receipt = read(R / 'RECEIPT.json')
        samples = read(R / 'TELEMETRY.json')
        start = read(R / 'SESSION_START.json')['started_utc']
        for index, sample in enumerate(samples):
            xml = ET.parse(R / f'telemetry_{index:04d}.xml').getroot().find('gpu')
            telemetry.append({'session': name, 'sample': index, 'utc': sample['utc'],
                'owned_PID': sample['owned_PID'], 'sample_elapsed_s': sample['elapsed_s'],
                'temperature_C': sample['temperature_C'], 'free_MiB': sample['free_MiB'],
                'reported_utilization_percent': sample['utilization_percent'],
                'performance_state': xml.findtext('performance_state', 'UNKNOWN'),
                'graphics_clock': xml.findtext('clocks/graphics_clock', 'UNKNOWN'),
                'sm_clock': xml.findtext('clocks/sm_clock', 'UNKNOWN'),
                'mem_clock': xml.findtext('clocks/mem_clock', 'UNKNOWN'),
                'clock_reasons_gpu_idle': xml.findtext('clocks_event_reasons/clocks_event_reason_gpu_idle', 'UNKNOWN'),
                'query_or_kernel_timestamp_alignment': 'UNKNOWN; context-owner sample is not per-request timing'})
        sequence = []
        for item in receipt['completed']:
            c = item['case']; sequence.append(c['mode'])
            command = read(R / f"{item['index']:02d}.command.json")
            assert command['preexisting_TCSC_variables_inherited'] is False
            assert sha((R / f"{item['index']:02d}.distances.bin").read_bytes()) == item['distance_sha256']
            rows = [x for x in item['results'] if x['kind'] == 'BFS']
            b = next(x for x in item['results'] if x['kind'] == 'BATCH')
            if c['phase'] != 'EXPLORATORY_TIMING':
                continue
            previous = 0.0
            for row in rows:
                requests.append({'session': name, 'worker': item['index'], 'block': c['block'], 'mode': c['mode'],
                    'delivered_increment_ms': row['owned_ready_prefix_ms'] - previous, **row})
                previous = row['owned_ready_prefix_ms']
            event = sum(x['stream_interval_ms'] for x in rows)
            copy = sum(x['return_copy_ms'] for x in rows)
            w = {'session': name, 'worker': item['index'], 'block': c['block'], 'mode': c['mode'],
                'q32_owned_prefix_ms': rows[-1]['owned_ready_prefix_ms'],
                'sum_stream_intervals_ms_not_busy_time': event, 'sum_return_allocation_copy_ms': copy,
                'remainder_ms_not_causally_localized': rows[-1]['owned_ready_prefix_ms'] - event - copy,
                'first_query_delivered_ms': rows[0]['owned_ready_prefix_ms'],
                'queries_1_to_31_mean_delivered_ms': (rows[-1]['owned_ready_prefix_ms'] - rows[0]['owned_ready_prefix_ms']) / 31,
                'kernel_launches': sum(x['kernel_launches'] for x in rows),
                'CPU_reconstructed_edge_tests_not_traffic': sum(x['reconstructed_edge_tests'] for x in rows),
                **{k: v for k, v in b.items() if k not in ['kind', 'status', 'q', 'mode']}}
            workers.append(w)
            lookup[name, c['block'], c['mode']] = (w, rows, normalized_argv(command['command'], name))
        schedules.append({'session': name, 'started_utc': start, 'worker_mode_sequence': sequence,
                          'smoke_workers': sum(x['case']['phase'] == 'SMOKE' for x in receipt['completed']),
                          'unverified_isolation_contract': receipt['contract']})
        for block in [0, 1]:
            if (name, block, 5) in lookup:
                d, p = lookup[name, block, 5][0], lookup[name, block, 7][0]
                pairs.append({'session': name, 'block': block, 'Direction_ms': d['q32_owned_prefix_ms'],
                              'lean_Push_ms': p['q32_owned_prefix_ms'],
                              'D_over_P': d['q32_owned_prefix_ms'] / p['q32_owned_prefix_ms']})
    csv_write(O / 'WORKER_COMPONENTS.csv', workers)
    csv_write(O / 'REQUEST_COMPONENTS.csv', requests)
    csv_write(O / 'RECORDED_TELEMETRY_ONLY.csv', telemetry)
    csv_write(O / 'Q32_PAIRS.csv', pairs)
    save(O / 'SCHEDULES.json', schedules)
    changes, per_request, segments = [], [], []
    signature_fields = ['source', 'query', 'seen', 'levels', 'reason', 'remaining_in', 'remaining_in_known',
                        'visit_bound', 'kernel_launches', 'reconstructed_edge_tests',
                        'reconstructed_push_rows', 'reconstructed_pull_candidates']
    for name in ['S2', 'S3']:
        for block in [0, 1]:
            row = {'new_session': name, 'block_label': block, 'design_equivalence': 'NOT_EXACT_REPLICATION; ORDER_OR_HISTORY_DIFFERS'}
            for mode, label in [(5, 'Direction'), (7, 'Push')]:
                old, oldq, oldcmd = lookup['S1', block, mode]
                new, newq, newcmd = lookup[name, block, mode]
                assert oldcmd == newcmd
                assert all(all(a[k] == b[k] for k in signature_fields) for a, b in zip(oldq, newq))
                oldout = read(I / 'S1/raw/RECEIPT.json')['completed'][old['worker']]['distance_sha256']
                newout = read(I / name / 'raw/RECEIPT.json')['completed'][new['worker']]['distance_sha256']
                assert oldout == newout
                for metric in ['q32_owned_prefix_ms', 'sum_stream_intervals_ms_not_busy_time',
                               'sum_return_allocation_copy_ms', 'remainder_ms_not_causally_localized',
                               'context_setup_transfer_ms', 'cpu_reverse_build_ms', 'graph_load_ms']:
                    row[label + '_' + metric + '_old'] = old[metric]
                    row[label + '_' + metric + '_new'] = new[metric]
                    row[label + '_' + metric + '_delta'] = new[metric] - old[metric]
                row[label + '_time_factor_new_over_old'] = new['q32_owned_prefix_ms'] / old['q32_owned_prefix_ms']
                for a, b in zip(oldq, newq):
                    per_request.append({'new_session': name, 'block_label': block, 'mode': mode, 'query': a['query'],
                        'source': a['source'], 'old_wall_ms': a['wall_ms'], 'new_wall_ms': b['wall_ms'],
                        'wall_delta_ms': b['wall_ms'] - a['wall_ms'],
                        'old_event_interval_ms_not_busy': a['stream_interval_ms'],
                        'new_event_interval_ms_not_busy': b['stream_interval_ms'],
                        'old_return_allocation_copy_ms': a['return_copy_ms'], 'new_return_allocation_copy_ms': b['return_copy_ms'],
                        'reported_final_counters_launches_and_reconstructed_work_equal': True})
                for start, stop in [(0, 1), (1, 8), (8, 16), (16, 24), (24, 32)]:
                    segments.append({'new_session': name, 'block_label': block, 'mode': mode,
                        'query_start': start, 'query_stop_exclusive': stop,
                        'old_wall_sum_ms': sum(x['wall_ms'] for x in oldq[start:stop]),
                        'new_wall_sum_ms': sum(x['wall_ms'] for x in newq[start:stop])})
            row['D_over_P_ratio_factor_new_over_old'] = row['Direction_time_factor_new_over_old'] / row['Push_time_factor_new_over_old']
            changes.append(row)
    csv_write(O / 'ABSOLUTE_CHANGE_VS_S1.csv', changes)
    csv_write(O / 'REQUEST_CHANGE_VS_S1.csv', per_request)
    csv_write(O / 'SEGMENT_CHANGE_VS_S1.csv', segments)
    summary = {'status': 'CPU_RECORD_AUDIT_COMPLETE', 'new_GPU_queries_or_dispatches': 0,
        'new_CPU_benchmarks_or_accuracy_runs': 0, 'new_compilations': 0, 'original_files_modified': False,
        'scope': 'Same byte-pinned ready consumer, differing execution designs and unverified regimes',
        'same_binary_source_inputs': True, 'same_reported_work_and_output_hashes': True,
        'same_normalized_commands_per_mode': True, 'same_explicit_environment_assignment_source': True,
        'full_environment_and_working_directory': 'UNKNOWN', 'algorithm_improvement': 'NO_CODE_CHANGE',
        'Direction_absolute_new_over_old_range': [min(x['Direction_time_factor_new_over_old'] for x in changes), max(x['Direction_time_factor_new_over_old'] for x in changes)],
        'Push_absolute_new_over_old_range': [min(x['Push_time_factor_new_over_old'] for x in changes), max(x['Push_time_factor_new_over_old'] for x in changes)],
        'Direction_query_wall_lower_count_of_128': sum(x['new_wall_ms'] < x['old_wall_ms'] for x in per_request if x['mode'] == 5),
        'unexplained_clock_cache_host_or_foreign_activity_cause': 'UNKNOWN',
        'recommendation': 'CHECK_MEASUREMENT_REGIME_BEFORE_PREPARATION_INCLUSIVE_EVALUATION',
        'experimentally_identified_Hardware_or_preparation_cause': False,
        'S1_ratios_retained': [x['D_over_P'] for x in pairs if x['session'] == 'S1'],
        'S2_S3_ratios_retained': [x['D_over_P'] for x in pairs if x['session'] != 'S1'],
        'telemetry_samples_reparsed_no_new_query': len(telemetry)}
    save(O / 'SUMMARY.json', summary)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['capture', 'analyze'])
    parser.add_argument('--workspace', type=Path, default=P.parent)
    parser.add_argument('--output', default='calculations')
    args = parser.parse_args()
    capture(args.workspace) if args.action == 'capture' else analyze(args.output)
