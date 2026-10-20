#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[1]
rows=json.loads((P/'MANIFEST.json').read_text())
for row in rows:
 p=(P/row['path']).resolve()
 assert p.is_relative_to(P), 'unsafe manifest path'
 assert p.is_file(),row['path']
 raw=p.read_bytes();assert len(raw)==row['bytes'],row['path']
 assert hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
print(json.dumps({'status':'PASS','hashed_files':len(rows)}))
