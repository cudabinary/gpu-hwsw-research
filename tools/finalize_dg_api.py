"""Preserve exact runtime binaries and hash the completed research checkpoint."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/dg_api_20261021';BUILD=ROOT/'build/dg_api_20261021'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def entry(p):return dict(bytes=p.stat().st_size,sha256=sha(p))
def main():
    assert json.loads((OUT/'BENCHMARK_COMPLETED.json').read_text())['status']=='PASS'
    for prefix in ('FROZEN','PROTECTED','PREVIOUS'):
        assert json.loads((OUT/(prefix+'_BEFORE.json')).read_text())==json.loads((OUT/(prefix+'_AFTER.json')).read_text())
    binaries=[ROOT/'build'/n for n in ('main_client','libgraph.so','baseline.so','rcc_table.so','rcc_last.so')]+[BUILD/'service']+sorted(BUILD.glob('*.so'))
    pinned=json.loads((OUT/'PINS.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in pinned.items())
    frozen=json.loads((OUT/'FROZEN_AFTER.json').read_text());assert all(sha(Path(p))==h for p,h in frozen.items())
    archive=OUT/'RUNTIME_BINARIES.tar.gz'
    if not archive.exists():
        with tarfile.open(archive,'w:gz') as t:
            for p in binaries:t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    with tarfile.open(archive,'r:gz') as t:
        for p in binaries:
            data=t.extractfile(str(p.relative_to(ROOT))).read();assert hashlib.sha256(data).hexdigest()==sha(p)
        assert len(t.getmembers())==len(binaries)
    (OUT/'RUNTIME_BINARIES.json').write_text(json.dumps(dict(archive=entry(archive),files={str(p.relative_to(ROOT)):entry(p) for p in binaries},MAIN_rebuilt=False),indent=2)+'\n')
    paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='ARTIFACT_SHA256.json']
    paths+=list((ROOT/'research').glob('dg_api*'))+[ROOT/'research/DG_API_PROTOCOL.json',ROOT/'research/DG_API_RESULTS.md']
    paths+=[ROOT/'tools'/n for n in ('run_dg_api.py','analyze_dg_api.py','finalize_dg_api.py')]
    paths+=[ROOT/p for p in ('.gitattributes','RCC_STATUS.md','TRACK_STATUS.md','HANDOFF_RCC.md','START_RCC_CODEX.md')]
    manifest=dict(schema_version=1,parent_commit='5c489f154d4c7c0bb587972ee307fcaf03a313e2',files={str(p.relative_to(ROOT)):entry(p) for p in sorted(paths)})
    (OUT/'ARTIFACT_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',artifacts=len(manifest['files']),runtime_binaries=len(binaries),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive))))
if __name__=='__main__':main()
