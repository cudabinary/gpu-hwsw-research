"""GPU-free, read-only verification of an extracted S2/S3 delivery."""
from pathlib import Path
import csv, hashlib, json, math

P = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    plan = json.loads((P / 'config/PLAN.json').read_text())
    assert sha(P / 'config/PLAN.json') == 'cbb1459e2540e0ed8598bc681647a93e27d8c4003a9d15c98167e859944d12a4'
    for rel, digest in plan['pins'].items():
        assert sha(P / rel) == digest, rel
    summary = json.loads((P / 'results/analysis_complete/SUMMARY.json').read_text())
    published = list(csv.DictReader((P / 'results/analysis_complete/paired_ratios.csv').open(newline='')))
    arrays = workers = cancels = launches = 0
    pairs = []
    for name in ['S1', 'S2', 'S3']:
        root = P / ('historical/S1' if name == 'S1' else 'results/' + name)
        receipt = json.loads((root / 'RECEIPT.json').read_text())
        timing = {}
        for item in receipt['completed']:
            case = item['case']
            bfs = [x for x in item['results'] if x['kind'] == 'BFS']
            batch = next(x for x in item['results'] if x['kind'] == 'BATCH')
            if name != 'S1':
                arrays += len(bfs)
                workers += 1
                cancels += batch['cancel_tests']
                launches += sum(x['kernel_launches'] for x in bfs) + batch['cancel_tests']
                assert item['Python_full_array_check'] == 'PASS'
                assert sha(root / f"{item['index']:02d}.distances.bin") == item['distance_sha256']
            if case['phase'] == 'EXPLORATORY_TIMING':
                timing[case['block'], case['mode']] = bfs
        for block in [0, 1]:
            for q in [1, 2, 8, 32]:
                push = timing[block, 7][q-1]['owned_ready_prefix_ms']
                direction = timing[block, 5][q-1]['owned_ready_prefix_ms']
                actual = next(x for x in published if x['session'] == name and int(x['block']) == block and int(x['q']) == q)
                assert math.isclose(float(actual['Direction_over_lean']), direction / push, rel_tol=1e-12)
                assert float(actual['lean_Push7_ms']) == push
                assert float(actual['Direction5_ms']) == direction
                if q == 32:
                    pairs.append({'session': name, 'block': block, 'D_over_P': direction / push})
    assert (workers, arrays, cancels, launches) == (12, 268, 4, 2036)
    assert summary['new_full_BFS_arrays_checked'] == arrays
    campaign = json.loads((P / 'results/CAMPAIGN/RECEIPT.json').read_text())
    assert campaign['whole_campaign_wall_seconds_including_gap'] < 600
    print(json.dumps({'status': 'OFFLINE_REPRODUCTION_PASS', 'GPU_queries_or_dispatches': 0,
        'workers': workers, 'BFS_arrays_checked_twice_not_double_counted': arrays,
        'init_only_cancellations': cancels, 'kernel_submissions': launches,
        'all_execution_pins_and_output_binary_hashes_match': True,
        'q32_pairs_including_historical_adverse_order': pairs,
        'contract': 'ISOLATION_UNVERIFIED'}, indent=2))

if __name__ == '__main__':
    main()
