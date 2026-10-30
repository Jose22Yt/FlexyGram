"""Exact Beta delivery preparation on PR140; source audit only, not APK approval."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='72f7e7f1e8600a85ab2539e04197b2fc9a6742a1'
MANIFEST=ROOT/'tools/beta_release/review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
@lru_cache(maxsize=128)
def original(path):
    r=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return r.stdout if r.returncode==0 else b''
def restore(path,data):
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
    current=spec()
    if current['base']!=BASE:raise ValueError('Wrong Beta delivery preparation base')
    for name,expected in current['reviewed'].items():
        file=ROOT/name;data=file.read_bytes() if file.is_file() else b''
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed Beta delivery bytes: '+name)
        if restore(name,data+b'UNKNOWN')!=data+b'UNKNOWN':raise ValueError('Unknown mutation accepted')
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
    changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unknown Beta delivery scope: '+repr(sorted(changed-paths())))
    print('PASS exact Beta preparation; official private inputs/APK/device acceptance separate')
if __name__=='__main__':verify_current()
