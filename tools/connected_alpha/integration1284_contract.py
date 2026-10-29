"""Exact iOS27 integration delta. Historical manifests and unknown-byte rejection stay intact."""
from pathlib import Path
from functools import lru_cache
import hashlib, json, subprocess
ROOT = Path(__file__).resolve().parents[2]
BASE = 'e00b33e806921017ad74ff50eb5ec88607131d9c'
MANIFEST = ROOT/'tools/connected_alpha/integration1284_review.json'
def spec(): return json.loads(MANIFEST.read_text())
def paths(): return frozenset(spec()['paths'])
@lru_cache(maxsize=256)
def original(path):
    result = subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return result.stdout if result.returncode == 0 else b''
def restore(path, data):
    expected = spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest() == expected else data
def historical_bytes(path): return restore(path,(ROOT/path).read_bytes())
def verify_current():
    s = spec()
    if s['base'] != BASE: raise ValueError('Incorrect integration base')
    for path, expected in s['reviewed'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != expected:
            raise ValueError('Unreviewed iOS27 source: '+path)
    changed = set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths(): raise ValueError('Unreviewed iOS27 scope: '+repr(sorted(changed-paths())))
    print('PASS exact iOS27 integration scope; Android/server/device acceptance is separate')
if __name__ == '__main__': verify_current()
