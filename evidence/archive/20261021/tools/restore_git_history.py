"""Restore a bundle with its ORIGINAL shallow boundary; never invent history.

All writes are to a new derived bare repository. No fetch/network, source Git
mutation, replacement objects, grafts, fsck suppression, or missing-object waiver.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess


def restore_bundle(git, bundle, destination, shallow_ids=(), expected_sha256=None):
    git, bundle, destination = Path(git), Path(bundle), Path(destination)
    if destination.exists():
        raise RuntimeError('GIT_RESTORE_DESTINATION_EXISTS')
    if expected_sha256 is not None and hashlib.sha256(bundle.read_bytes()).hexdigest() != expected_sha256:
        raise RuntimeError('RESTORED_BUNDLE_SHA256_MISMATCH')
    if any(not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', item) for item in shallow_ids):
        raise RuntimeError('INVALID_ORIGINAL_SHALLOW_BOUNDARY')
    destination.parent.mkdir(parents=True, exist_ok=True)
    logs = destination.parent / (destination.name + '.validation_logs')
    logs.mkdir(exist_ok=False)
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY',
                 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_SHALLOW_FILE', 'GIT_REPLACE_REF_BASE'):
        env.pop(name, None)
    records = []
    def run(args, label, stdin=None, input=None):
        command = [str(git), '-c', 'core.longpaths=true', *args]
        result = subprocess.run(command, stdin=stdin, input=input, capture_output=True, env=env, timeout=120)
        (logs / (label + '.stdout.log')).write_bytes(result.stdout)
        (logs / (label + '.stderr.log')).write_bytes(result.stderr)
        records.append({'command': command, 'returncode': result.returncode, 'label': label})
        (logs / 'commands.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        if result.returncode:
            raise RuntimeError('RESTORED_GIT_CHECK_FAILED_' + label.upper())
        return result.stdout
    heads = run(['bundle', 'list-heads', str(bundle)], 'bundle_heads').decode('ascii').splitlines()
    refs = []
    for line in heads:
        oid, name = line.split(' ', 1)
        if not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', oid):
            raise RuntimeError('INVALID_BUNDLE_REF_OBJECT')
        if name != 'HEAD' and ((not name.startswith('refs/') and not re.fullmatch(r'worktrees/[A-Za-z0-9_.-]+/HEAD', name)) or any(c in name for c in '\r\n\x00 ')):
            raise RuntimeError('INVALID_BUNDLE_REF_NAME')
        refs.append((oid, name))
    if shallow_ids:
        init = ['init', '--bare', '--template=', str(destination)]
        if refs and len(refs[0][0]) == 64:
            init.insert(2, '--object-format=sha256')
        run(init, 'init_bare')
        # A raw handle is required: a buffered readline may advance the OS file
        # descriptor past PACK, while the child inherits that OS position.
        with bundle.open('rb', buffering=0) as handle:
            magic = handle.readline()
            if magic not in (b'# v2 git bundle\n', b'# v3 git bundle\n'):
                raise RuntimeError('UNSUPPORTED_BUNDLE_HEADER')
            while True:
                line = handle.readline(1024 * 1024)
                if line == b'\n':
                    break
                if not line or line.startswith(b'-'):
                    raise RuntimeError('BUNDLE_HAS_EXTERNAL_PREREQUISITE')
            run(['-C', str(destination), 'index-pack', '--stdin', '--fix-thin'], 'index_pack', stdin=handle)
        # This is the exact boundary read from the original shallow repository.
        (destination / 'shallow').write_text('\n'.join(sorted(set(shallow_ids))) + '\n', encoding='ascii')
        updates = ''.join('create ' + name + ' ' + oid + '\n' for oid, name in refs if name.startswith('refs/'))
        run(['-C', str(destination), 'update-ref', '--stdin'], 'restore_refs', input=updates.encode('ascii'))
        head = next((oid for oid, name in refs if name == 'HEAD'), None)
        if head:
            (destination / 'HEAD').write_text(head + '\n', encoding='ascii')
        boundary_objects = run(['-C', str(destination), 'cat-file', '--batch-check'], 'boundary_objects',
                               input=('\n'.join(shallow_ids) + '\n').encode('ascii'))
        if b' missing' in boundary_objects:
            raise RuntimeError('ORIGINAL_SHALLOW_BOUNDARY_OBJECT_MISSING')
    else:
        run(['clone', '--bare', '--template=', str(bundle), str(destination)], 'clone_bare')
    run(['-C', str(destination), 'fsck', '--full'], 'fsck_full')
    objects = run(['-C', str(destination), 'cat-file', '--batch-check'], 'all_reference_objects',
                  input=('\n'.join(oid for oid, name in refs) + '\n').encode('ascii'))
    if b' missing' in objects:
        raise RuntimeError('RESTORED_GIT_REFERENCE_OBJECT_MISSING')
    run(['-C', str(destination), 'rev-list', '--all', '--count'], 'traverse_history')
    return {'git_history_restore_and_fsck': 'PASS', 'git_bundle_reference_objects': 'PASS',
            'git_clone_and_fsck': 'PASS' if not shallow_ids else 'ORIGINAL_SHALLOW_RECONSTRUCTION_AND_FSCK_PASS',
            'source_is_shallow': bool(shallow_ids), 'original_shallow_boundary_count': len(set(shallow_ids)),
            'upstream_history_before_boundary': 'NOT_IN_ORIGINAL' if shallow_ids else 'NOT_APPLICABLE',
            'raw_validation_logs': str(logs)}
