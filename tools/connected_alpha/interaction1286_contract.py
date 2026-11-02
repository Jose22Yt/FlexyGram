"""Exact Interaction 2.0 delta over the physically tried Alpha1285. Audit-only projections."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='e0c8e1b78acc120481cc9675de149771f59ddd6c'
MANIFEST=ROOT/'tools/connected_alpha/interaction1286_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():
 from identity_beta_contract import paths as identity_paths
 return frozenset(spec()['paths']) | identity_paths()
@lru_cache(maxsize=256)
def original(path):
 r=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
 return r.stdout if r.returncode==0 else b''
def restore(path,data):
 from identity_beta_contract import restore as identity_restore
 data=identity_restore(path,data)
 expected=spec()['reviewed'].get(str(path))
 return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
 from identity_beta_contract import verify_current as verify_identity, restore as identity_restore
 verify_identity()
 s=spec()
 if s['base']!=BASE:raise ValueError('Incorrect interaction base')
 for path,expected in s['reviewed'].items():
  file=ROOT/path;data=identity_restore(path,file.read_bytes() if file.is_file() else b'')
  if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed Interaction2 source: '+path)
 changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 if changed-paths():raise ValueError('Unknown Interaction2 scope: '+repr(sorted(changed-paths())))
 print('PASS exact Interaction2 source; isolated graphics do not imply physical acceptance')
if __name__=='__main__':verify_current()
