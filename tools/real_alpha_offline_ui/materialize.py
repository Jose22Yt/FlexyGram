#!/usr/bin/env python3
"""Materialize hash-locked source copies, never patch the shared Android sources."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path('TMessagesProj/build/generated/flexygram-offline-dialogs-ui/java')
PATCH = Path('patches/real-alpha-offline-ui/0001-native-dialogs-offline-ui.patch')
SOURCES = ('org/telegram/ui/DialogsActivity.java', 'org/telegram/ui/Adapters/DialogsAdapter.java',
           'org/telegram/ui/Adapters/DialogsSearchAdapter.java')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def materialize(root=ROOT, check=False):
    root = Path(root).resolve()
    lock = json.loads((root / 'tools/real_alpha_offline_ui/sources.json').read_text())
    if set(lock['sources']) != set(SOURCES):
        raise ValueError('unexpected source inventory')
    patch = (root / PATCH).read_bytes()
    if digest(patch) != lock['patch_sha256']:
        raise ValueError('patch hash mismatch')
    with tempfile.TemporaryDirectory(prefix='flexygram-offline-ui-') as tmp:
        stage = Path(tmp)
        for source in SOURCES:
            relative = Path('TMessagesProj/src/main/java') / source
            data = (root / relative).read_bytes()
            if digest(data) != lock['sources'][source]['original_sha256']:
                raise ValueError('original hash mismatch: ' + source)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for extra in (['--check'], []):
            subprocess.run(['git', 'apply', '--whitespace=error', *extra, '-'], input=patch,
                           cwd=stage, check=True, capture_output=True)
        generated = {}
        for source in SOURCES:
            data = (stage / 'TMessagesProj/src/main/java' / source).read_bytes()
            if digest(data) != lock['sources'][source]['overlay_sha256']:
                raise ValueError('overlay hash mismatch: ' + source)
            generated[source] = data
        destination = root / OUTPUT
        # No redirects into the shared source tree or any other worktree.
        if destination.resolve() != destination:
            raise ValueError('symlinked output directory')
        if destination.exists():
            actual = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
            if actual != set(SOURCES):
                raise ValueError('unexpected generated file inventory')
            for source, data in generated.items():
                path = destination / source
                if path.is_symlink() or path.read_bytes() != data:
                    raise ValueError('existing overlay differs: ' + source)
        elif check:
            raise ValueError('overlay not materialized')
        else:
            for source, data in generated.items():
                target = destination / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    return {'sources': len(SOURCES), 'verified': True, 'output': str(OUTPUT)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(materialize(check=args.check), sort_keys=True))
