"""Exact Beta integration audit; historical source projections never run on Android."""
from pathlib import Path
from functools import lru_cache
import hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='d5099523f1f97720ac6b2180466ae18673f2c8fb'
MANIFEST=ROOT/'tools/beta_integration/review.json'
def spec(): return json.loads(MANIFEST.read_text())
def paths():
    from beta_release_contract import paths as next_paths
    return frozenset(spec()['paths'])|next_paths()
@lru_cache(maxsize=128)
def original(path):
    p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return p.stdout if p.returncode==0 else b''
def restore(path,data):
    from beta_release_contract import restore as next_restore
    data=next_restore(path,data)
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
    from beta_release_contract import verify_current as next_verify,restore as next_restore
    next_verify()
    current=spec()
    if current['base']!=BASE: raise ValueError('Wrong Beta integration base')
    for name,expected in current['reviewed'].items():
        file=ROOT/name;data=next_restore(name,file.read_bytes() if file.is_file() else b'')
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed Beta bytes: '+name)
        if restore(name,data+b'UNKNOWN')!=data+b'UNKNOWN':raise ValueError('Unknown Beta mutation accepted: '+name)
    changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unknown Beta scope: '+repr(sorted(changed-paths())))
    print('PASS exact Beta integration source audit; APK/device acceptance separate')
if __name__=='__main__':verify_current()
