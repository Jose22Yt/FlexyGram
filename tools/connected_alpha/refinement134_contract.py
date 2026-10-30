"""Exact, additive Signature iOS 27 overlay over reviewed Work1 PR133.

Only Git blob-identical reviewed bytes can be projected back to PR133 for
historical SHA-256 checks. New or unknown bytes are never silently accepted.
This audit is source-only and never runs inside Android.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '49f91b58be48765abe02f7c3f33a5c94c93dbc52'
MANIFEST = ROOT / 'tools/refinement134/review.json'

def spec():
    return json.loads(MANIFEST.read_text())

def paths():
    return frozenset(spec()['paths'])

def blob_sha(data):
    header = b'blob ' + str(len(data)).encode() + b'\x00'
    return hashlib.sha1(header + data).hexdigest()

@lru_cache(maxsize=128)
def original(path):
    result = subprocess.run(['git', 'show', BASE + ':' + str(path)],
                            cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else b''

def restore(path, data):
    reviewed = spec()['reviewed'].get(str(path))
    if reviewed is not None and blob_sha(data) == reviewed:
        return original(path)
    return data

def verify_current():
    s = spec()
    if s['base'] != BASE:
        raise ValueError('Wrong Signature iOS 27 overlay base')
    for path, expected in s['reviewed'].items():
        file = ROOT / path
        data = file.read_bytes() if file.is_file() else b''
        if blob_sha(data) != expected:
            raise ValueError('Unreviewed Signature refinement delta: ' + path)
        tampered = data + b'\nUNREVIEWED\n'
        if restore(path, tampered) != tampered:
            raise ValueError('Unknown Signature refinement accepted: ' + path)
    changed = set(subprocess.check_output(
        ['git', 'diff', '--no-renames', BASE, '--name-only'],
        cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard'],
        cwd=ROOT, text=True).splitlines())
    if changed - paths():
        raise ValueError('Unknown Signature refinement scope: ' + repr(sorted(changed - paths())))
    print('PASS exact Signature iOS 27 overlay over Work1 PR133; physical validation pending')

if __name__ == '__main__':
    verify_current()
