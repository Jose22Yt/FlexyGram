"""Reviewed integration over PR119; historical manifests remain immutable."""
from pathlib import Path
from functools import lru_cache
import hashlib, json, subprocess
ROOT = Path(__file__).resolve().parents[2]
BASE = '2fd05e955c494a9eb0112c23e2ff9511a459e6c8'
MANIFEST = ROOT / 'tools/connected_alpha/integration1282_review.json'
def spec():
    return json.loads(MANIFEST.read_text())
def paths():
    from alpha1283_contract import paths as next_paths
    return frozenset(spec()['paths']) | next_paths()
@lru_cache(maxsize=128)
def original(path):
    result = subprocess.run(['git', 'show', BASE + ':' + str(path)], cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else b''
def restore(path, data):
    from alpha1283_contract import restore as next_restore
    data=next_restore(path,data)
    expected = spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest() == expected else data
def historical_bytes(path):
    return restore(path, (ROOT/path).read_bytes())
def verify_current():
    from alpha1283_contract import verify_current as verify_next, restore as next_restore
    verify_next()
    s = spec()
    if s['base'] != BASE:
        raise ValueError('Incorrect integration base')
    for path, expected in s['reviewed'].items():
        if hashlib.sha256(next_restore(path,(ROOT/path).read_bytes())).hexdigest() != expected:
            raise ValueError('Unreviewed integration: ' + path)
    changed = set(subprocess.check_output(['git', 'diff', BASE, '--name-only'], cwd=ROOT, text=True).splitlines())
    if changed - paths():
        raise ValueError('Unreviewed integration scope: ' + repr(sorted(changed-paths())))
    print('PASS: reviewed integration; physical acceptance remains pending')
if __name__ == '__main__':
    verify_current()
