from native_motion_restore_contract import read_current
"""Exact independently reviewed motion delta above Work1; unknown mutations never normalize away."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='14e586b4ddb7a686f39cda3cb175920c49cecf11'
MANIFEST=ROOT/'tools/connected_alpha/motion_review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
def restore(path,data):
 from integration1279_contract import project
 data=project("motion",path,data)
 expected=spec()['reviewed'].get(str(path))
 if expected is None or hashlib.sha256(data).hexdigest()!=expected:return data
 p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
 return p.stdout if p.returncode==0 else b''
def restore_navigation(path,data):
 # Historical release guards accept only the exact reviewed navigation delta.
 return restore(path,data) if str(path)=='TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java' else data
def verify_current():
 from integration1279_contract import project,verify_current as verify_integration,paths as integration_paths
 verify_integration()
 s=spec()
 for name,sha in s['reviewed'].items():
  if hashlib.sha256(project("motion",name,read_current(name))).hexdigest()!=sha:raise ValueError('Unreviewed Motion source: '+name)
 changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 if changed-paths()-integration_paths():raise ValueError('Unreviewed Motion scope: '+str(sorted(changed-paths())))
 print('PASS: independently reviewed motion delta; device/performance acceptance remains pending.')
if __name__=='__main__':verify_current()
