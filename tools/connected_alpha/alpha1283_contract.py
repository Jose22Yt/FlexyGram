"""Exact continuation above PR122. Historical reviews remain immutable; no runtime projection."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='bb3af73e085f3cdb3e9e92f35f6d1b692c04afcb'
MANIFEST=ROOT/'tools/connected_alpha/alpha1283_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
@lru_cache(maxsize=128)
def original(path):
    p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return p.stdout if p.returncode==0 else b''
def restore(path,data):
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data

def verify_current():
    s=spec()
    if s['base']!=BASE:raise ValueError('Incorrect continuation base')
    for name,expected in s['reviewed'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Unreviewed Alpha1283 source: '+name)
    changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unreviewed Alpha1283 scope: '+repr(sorted(changed-paths())))
    print('PASS exact Alpha1283 continuation; server/device acceptance remains separate')
if __name__=='__main__':verify_current()
