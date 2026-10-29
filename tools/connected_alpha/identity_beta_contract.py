"""Exact identity-only overlay; prior source audits retain their original SHA contracts."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '258dd3590f40ca0083a4b7bad6b413433c4e2c14'
MANIFEST = ROOT / 'tools/identity/review.json'


def spec():
    return json.loads(MANIFEST.read_text())


def paths():
    return frozenset(spec()['paths'])


@lru_cache(maxsize=256)
def original(path):
    result = subprocess.run(['git', 'show', BASE + ':' + str(path)], cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else b''


def restore(path, data):
    expected = spec()['reviewed'].get(str(path))
    if expected and hashlib.sha256(data).hexdigest() == expected:
        return original(path)
    return data


def verify_current():
    current = spec()
    if current['base'] != BASE:
        raise ValueError('Incorrect identity base')
    for path, expected in current['reviewed'].items():
        file = ROOT / path
        data = file.read_bytes() if file.is_file() else b''
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Unreviewed identity source: ' + path)
    changed = set(subprocess.check_output(['git', 'diff', '--no-renames', BASE, '--name-only'], cwd=ROOT, text=True).splitlines())
    if changed - paths():
        raise ValueError('Unknown identity scope: ' + repr(sorted(changed - paths())))
