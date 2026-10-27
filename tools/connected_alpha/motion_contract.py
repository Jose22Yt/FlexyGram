"""Exact independently reviewed motion delta above Work1; unknown mutations never normalize away."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='a2d8f2bc06279aa5809f7574ea41646936556d2b'
MANIFEST=ROOT/'tools/connected_alpha/motion_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
def restore(path,data):
 expected=spec()['reviewed'].get(str(path))
 if expected is None or hashlib.sha256(data).hexdigest()!=expected:return data
 p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
 return p.stdout if p.returncode==0 else b''
def verify_current():
 s=spec()
 for name,sha in s['reviewed'].items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Unreviewed Motion source: '+name)
 changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 if changed-paths():raise ValueError('Unreviewed Motion scope: '+str(sorted(changed-paths())))
 print('PASS: independently reviewed motion delta; device/performance acceptance remains pending.')
if __name__=='__main__':verify_current()
