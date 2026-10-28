"""Exact Alpha1280 overlay over reviewed PR113; behavioral tests run actual production."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='1915f26039f53f838c06b107c0f68e115c1b014c'
MANIFEST=ROOT/'tools/connected_alpha/alpha1280_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():
    from alpha1281_contract import paths as next_paths
    return frozenset(spec()['paths']) | next_paths()
@lru_cache(maxsize=256)
def original(path):
    p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return p.stdout if p.returncode==0 else b''
def restore(path,data):
    from alpha1281_contract import restore as next_restore
    data=next_restore(path,data)
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
    from alpha1281_contract import verify_current as verify_next, restore as next_restore
    verify_next()
    s=spec()
    if s['base']!=BASE:raise ValueError('Incorrect Alpha1280 base')
    for name,expected in s['reviewed'].items():
        if hashlib.sha256(next_restore(name,(ROOT/name).read_bytes())).hexdigest()!=expected:raise ValueError('Unreviewed Alpha1280 source: '+name)
    changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unreviewed Alpha1280 scope: '+repr(sorted(changed-paths())))
    print('PASS exact Alpha1280 overlay; physical performance acceptance remains separate.')
if __name__=='__main__':verify_current()
