"""Exact Smart Previews 2.0 overlay; historical reviews are retained byte-for-byte."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='55e3a47917604624d6998f56abe08265585412fa'
MANIFEST=ROOT/'tools/connected_alpha/alpha1281_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
@lru_cache(maxsize=256)
def original(path):
    p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return p.stdout if p.returncode==0 else b''
def restore(path,data):
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
    s=spec()
    if s['base']!=BASE:raise ValueError('Incorrect Alpha1281 base')
    for name,expected in s['reviewed'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Unreviewed Alpha1281 source: '+name)
    changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unreviewed Alpha1281 scope: '+repr(sorted(changed-paths())))
    print('PASS: exact reviewed Alpha1281 source; phone acceptance remains separate.')
if __name__=='__main__':verify_current()
