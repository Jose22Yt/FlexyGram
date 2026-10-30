"""Exact approved corrections over Alpha1284. Projections are audit-only, never runtime code."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='6003a8ce7114cb5f4f027b878fd34019cdad06b1'
MANIFEST=ROOT/'tools/connected_alpha/reconstruction1285_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():
    from interaction1286_contract import paths as next_paths
    return frozenset(spec()['paths'])|next_paths()
@lru_cache(maxsize=256)
def original(path):
    result=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return result.stdout if result.returncode==0 else b''
def read_current(path):
    file=ROOT/path
    if file.is_file():return file.read_bytes()
    if spec()['reviewed'].get(str(path))==hashlib.sha256(b'').hexdigest():return b''
    from work1_contract import spec as work1_spec
    if work1_spec()['reviewed'].get(str(path))==hashlib.sha256(b'').hexdigest():return b''
    from native_context135_contract import spec as current_spec
    if current_spec()['reviewed'].get(str(path))==hashlib.sha256(b'').hexdigest():return b''
    raise FileNotFoundError(file)
def restore(path,data):
    from interaction1286_contract import restore as next_restore
    data=next_restore(path,data)
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def prior_bytes(path):return restore(str(path),read_current(str(path)))
def verify_current():
    from interaction1286_contract import verify_current as verify_next,restore as next_restore
    verify_next()
    s=spec()
    if s['base']!=BASE:raise ValueError('Incorrect reconstruction base')
    for path,expected in s['reviewed'].items():
        if hashlib.sha256(next_restore(path,read_current(path))).hexdigest()!=expected:raise ValueError('Unreviewed reconstruction: '+path)
    changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unknown reconstruction scope: '+repr(sorted(changed-paths())))
    print('PASS exact reconstruction source and deletions; phone/real-server acceptance is separate')
if __name__=='__main__':verify_current()
