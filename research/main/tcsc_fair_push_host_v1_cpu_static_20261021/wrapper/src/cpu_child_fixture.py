"""Owned non-GPU protocol fixture. No CUDA or device module is imported."""
from pathlib import Path
import argparse, hashlib, json, os, sys, time

p = argparse.ArgumentParser()
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--case', required=True)
p.add_argument('--mode', type=int, required=True)
p.add_argument('--q', type=int, required=True)
a = p.parse_args()
r = a.directory
(r / 'ready').write_text(str(os.getpid() + int(a.case == 'bad_ready')))
start = time.monotonic()
while not (r / 'ack').exists():
    if time.monotonic() - start > 3:
        raise SystemExit(11)
    time.sleep(.01)
if (r / 'ack').read_text().strip() != str(os.getpid()):
    raise SystemExit(12)
if a.case == 'nonzero':
    print('CPU_SYNTHETIC_NONZERO', file=sys.stderr, flush=True)
    raise SystemExit(7)
if a.case in ['hang', 'cancel']:
    while True:
        time.sleep(.05)
payload = {'kind': 'CPU_CHILD_PROTOCOL_NOT_BFS', 'mode': a.mode, 'q': a.q,
           'logical_slots': list(range(a.q)), 'simulated_init_cancel': int(a.q == 3)}
digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
with (r / 'result.json').open('x') as f:
    json.dump({'payload': payload, 'sha256': '0'*64 if a.case == 'bad_output' else digest}, f)
if a.case != 'missing_release':
    print('CPU_CHILD_RELEASED_NO_CUDA', file=sys.stderr, flush=True)
