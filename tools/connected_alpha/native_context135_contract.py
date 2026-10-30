"""Exact native-context/default-Home overlay over reviewed PR134. Audit only, never Android."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='6ed4d9154a032eebd22e6c236701308e388bcb17'
MANIFEST=ROOT/'tools/native_context/review.json'
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
 if s['base']!=BASE:raise ValueError('Wrong native-context base')
 for name,expected in s['reviewed'].items():
  p=ROOT/name;data=p.read_bytes() if p.is_file() else b''
  if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed native-context bytes: '+name)
  if restore(name,data+b'UNKNOWN')!=data+b'UNKNOWN':raise ValueError('Unknown mutation accepted')
 changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
 if changed-paths():raise ValueError('Unknown native-context scope: '+repr(sorted(changed-paths())))
 print('PASS exact native-context/default-Home source overlay; physical acceptance separate')
if __name__=='__main__':verify_current()
