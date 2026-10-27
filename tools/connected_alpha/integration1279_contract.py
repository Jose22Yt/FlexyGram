"""Exact integration review; original PR manifests and historical bytes stay frozen.

Projection is allowed only for a byte-exact reviewed integrated file. Each
independent audit still checks its original snapshot, including unknown-edit
rejection. Behavioral/native tests continue to execute the integrated sources.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE='14e586b4ddb7a686f39cda3cb175920c49cecf11'
MANIFEST=ROOT/'tools/connected_alpha/integration1279_review.json'
PROJECTIONS=ROOT/'tools/connected_alpha/integration1279_projections.json'

def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
def sha(data):return hashlib.sha256(data).hexdigest()

@lru_cache(maxsize=512)
def baseline(path):
    result=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
    return result.stdout if result.returncode==0 else b''

@lru_cache(maxsize=512)
def blob(oid):
    return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)

def project(scope,path,data):
    path=str(path)
    expected=spec()['reviewed'].get(path)
    if expected is None or sha(data)!=expected:return data
    views=json.loads(PROJECTIONS.read_text())
    if views['base']!=BASE:raise ValueError('Incorrect integration projection base')
    oid=views['views'].get(scope,{}).get(path)
    return blob(oid) if oid else baseline(path)

def verify_current():
    s=spec()
    if s['base']!=BASE:raise ValueError('Incorrect Alpha1279 base')
    for path,expected in s['reviewed'].items():
        if sha((ROOT/path).read_bytes())!=expected:
            raise ValueError('Unreviewed Alpha1279 integrated source: '+path)
    changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unreviewed Alpha1279 scope: '+repr(sorted(changed-paths())))
    print('PASS: exact combined Alpha1279 sources; original PR reviews retained; device acceptance pending.')

if __name__=='__main__':verify_current()
