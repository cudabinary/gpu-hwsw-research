"""Existing-tool static host compile only; no CUDA API/device query."""
from pathlib import Path
import datetime, hashlib, json, subprocess

P = Path(__file__).resolve().parents[1]
def wsl(path):
    text = path.resolve().as_posix()
    return '/mnt/' + text[0].lower() + text[2:]

def main():
    output = P / 'build/owner_fair_v1.exe'
    assert not output.exists() and not (P / 'audit/COMPILE.json').exists()
    argv = ['wsl.exe', '-d', 'Ubuntu', '--', 'x86_64-w64-mingw32-g++', '-std=c++17',
            '-O2', '-static', '-I' + wsl(P / 'src'), '-I' + wsl(P / 'include'),
            '-I/usr/local/cuda-13.3/include', wsl(P / 'src/owner_fair_v1.cpp'), '-o', wsl(output)]
    start = datetime.datetime.now(datetime.timezone.utc)
    run = subprocess.run(argv, capture_output=True, timeout=180)
    (P / 'audit/compile.stdout.log').write_bytes(run.stdout)
    (P / 'audit/compile.stderr.log').write_bytes(run.stderr)
    row = {'status': 'STATIC_HOST_COMPILE_LINK_PASS' if run.returncode == 0 else 'COMPILE_FAILED',
           'argv': argv, 'exit_code': run.returncode, 'timeout_seconds': 180,
           'started_utc': start.isoformat(), 'new_CUDA_compilation': False,
           'new_GPU_queries_or_dispatches': 0}
    if run.returncode == 0:
        row['binary_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    (P / 'audit/COMPILE.json').write_text(json.dumps(row, indent=2))
    print(json.dumps(row, indent=2))
    raise SystemExit(run.returncode)

if __name__ == '__main__':
    main()
