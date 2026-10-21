"""Bounded compiled CPU checks and independent Python full-array verification."""
from pathlib import Path
from collections import deque
import hashlib, json, os, struct, subprocess

P = Path(__file__).resolve().parents[1]

def main():
    R = P / 'results/CPU_OWNER_CHECKS'
    R.mkdir(exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith('TCSC_')}
    exe = P / 'build/owner_fair_v1.exe'
    def call(name, args, output=None):
        e = dict(env)
        if output:
            e['TCSC_CPU_DISTANCE_OUT'] = str(output)
        command = [str(exe), *args]
        result = subprocess.run(command, env=e, capture_output=True, timeout=120)
        (R / (name + '.stdout.log')).write_bytes(result.stdout)
        (R / (name + '.stderr.log')).write_bytes(result.stderr)
        (R / (name + '.command.json')).write_text(json.dumps({'command': command,
            'action_class': 'CPU_ONLY', 'GPU_permits_inherited': False, 'timeout_seconds': 120}, indent=2))
        assert result.returncode == 0, name
        return json.loads(result.stdout)
    unit = call('fair_tests', ['--fair-tests'])
    abi = call('abi', ['--abi'])
    assert unit['status'] == 'FAIR_HOST_CPU_TEST_PASS' and not unit['driver_loaded'] and unit['GPU_launches'] == 0
    assert abi['View'] == 112 and abi['Counter'] == 24
    checks = []
    for fixture, n, q in [('gpu_micro7.edges', 7, 3), ('livejournal_sampled_4096.edges', 4096, 32)]:
        adj = [[] for _ in range(n)]
        for line in (P / 'fixtures' / fixture).read_text().splitlines():
            if line and line[0] not in '#%':
                a, b = map(int, line.split())
                adj[a].append(b)
        sources = [0, 1, 4] if q == 3 else [17*i for i in range(32)]
        exact = bytearray()
        for source in sources:
            distance = [-1]*n
            distance[source] = 0
            work = deque([source])
            while work:
                a = work.popleft()
                for b in adj[a]:
                    if distance[b] < 0:
                        distance[b] = distance[a] + 1
                        work.append(b)
            exact.extend(struct.pack('<' + 'i'*n, *distance))
        for mode in [7, 5]:
            name = f'n{n}_mode{mode}'
            output = R / (name + '.distances.bin')
            row = call(name, ['--cpu-check', str(P / 'fixtures' / fixture), str(n), str(mode), str(q)], output)
            assert output.read_bytes() == exact
            assert row['driver_loaded'] is False and row['GPU_launches'] == 0
            assert row['reverse_present'] == (mode == 5)
            if n == 4096:
                assert row['projected_device_payload_bytes'] == (275124 if mode == 7 else 501580)
                assert row['preparation_payload_bytes'] == (512 if mode == 7 else 225944)
            checks.append({'fixture': fixture, 'n': n, 'q': q, **row,
                'Python_full_arrays': 'PASS', 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'time_kind': 'ONE_SHOT_CPU_PREPARATION_NOT_GPU_PERFORMANCE'})
    result = {'status': 'COMPILED_CPU_AND_INDEPENDENT_PYTHON_PASS', 'unit': unit, 'abi': abi,
        'compiled_fixture_arrays': sum(x['q'] for x in checks), 'independent_Python_fixture_arrays': sum(x['q'] for x in checks),
        'checks': checks, 'new_GPU_queries_or_dispatches': 0, 'new_CUDA_compilations': 0}
    (R / 'SUMMARY.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
