"""Verify and preserve the supplied ZIP as data; never execute its commands."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import shutil
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/mnt/c/Users/정다빈/Downloads/RCC_SCOPE_DISTANCE_CPU_20261021.zip')
DEST=ROOT/'intake/rcc_scope_distance_20261021'
EXPECTED='c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c'

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

assert sha(SOURCE)==EXPECTED
assert not DEST.exists(), 'preserve existing intake; no overwrite'
DEST.mkdir(parents=True)
archive=DEST/'original.zip'
shutil.copyfile(SOURCE,archive)
assert sha(archive)==EXPECTED
receipt={'source_bytes':SOURCE.stat().st_size,'source_sha256':EXPECTED,'copied_archive_sha256':sha(archive),'document_instructions_executed':False}
with zipfile.ZipFile(archive) as z:
    entries=z.infolist()
    assert sum(i.file_size for i in entries)<100*1024*1024
    seen=set()
    for entry in entries:
        name=entry.filename
        p=PurePosixPath(name)
        assert not p.is_absolute() and '\\' not in name and all(t not in ('','.','..') and ':' not in t for t in p.parts)
        assert not stat.S_ISLNK(entry.external_attr>>16)
        assert name.casefold() not in seen
        seen.add(name.casefold())
    assert z.testzip() is None
    receipt.update(zip_crc='PASS',path_checks='PASS',entries=len(entries),uncompressed_bytes=sum(i.file_size for i in entries))
    prefix='RCC_SCOPE_CPU_MODULE_20261021/'
    manifest=json.loads(z.read(prefix+'MANIFEST.json'))
    expected={prefix+i['path']:i for i in manifest}
    actual={i.filename:i for i in entries if not i.is_dir() and i.filename!=prefix+'MANIFEST.json'}
    assert set(expected)==set(actual), 'manifest coverage mismatch'
    for name,item in expected.items():
        data=z.read(name)
        assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'], name
    receipt.update(manifest_files=len(expected),manifest_bytes_sha256='PASS',manifest_complete=True)
    for entry in entries:
        target=DEST/'package'/entry.filename
        assert target.resolve().is_relative_to((DEST/'package').resolve())
        if entry.is_dir(): target.mkdir(parents=True,exist_ok=True)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f: f.write(z.read(entry))
    package=DEST/'package/RCC_SCOPE_CPU_MODULE_20261021'
    assert all(sha(package/i['path'])==i['sha256'] and (package/i['path']).stat().st_size==i['bytes'] for i in manifest)
    upstream={
        'include/stop_bridge.hpp':'frozen/bridge/stop_bridge.hpp',
        'vendor/consumer/frozen/independent_builder.hpp':'frozen/consumer/independent_builder.hpp',
        'vendor/consumer/include/consumers.hpp':'frozen/consumer/consumers.hpp',
        'vendor/consumer/src/consumers.cpp':'frozen/consumer/consumers.cpp',
    }
    receipt['upstream_comparison']={a:dict(repository_file=b,identical=sha(package/a)==sha(ROOT/'vendor/rcc_20261021'/b)) for a,b in upstream.items()}
    receipt['shared_fixtures']={p.name:sha(p)==sha(ROOT/'vendor/rcc_20261021/fixtures'/p.name) for p in (package/'fixtures').glob('*.edges') if (ROOT/'vendor/rcc_20261021/fixtures'/p.name).exists()}
(DEST/'INTAKE.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
