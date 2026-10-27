"""Exact incremental sources above the physically validated Alpha1277; never rewrites its review."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='79ae7c6a4d52d3a787ca8dfddb11660d028bf24f'
MANIFEST=ROOT/'tools/connected_alpha/signature1278_review.json'
@lru_cache(maxsize=256)
def original(path):
 r=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
 return r.stdout if r.returncode==0 else b''
def restore(path,data):
 from motion_contract import restore as motion_restore
 data=motion_restore(path,data)
 expected=json.loads(MANIFEST.read_text())['reviewed'].get(str(path))
 return original(path) if expected is not None and hashlib.sha256(data).hexdigest()==expected else data
def paths():
 from motion_contract import paths as motion_paths
 return frozenset(json.loads(MANIFEST.read_text())['paths'])|motion_paths()
def verify_current():
 from motion_contract import verify_current as verify_motion,restore as motion_restore,paths as motion_paths
 verify_motion()
 spec=json.loads(MANIFEST.read_text())
 for name,expected in spec['reviewed'].items():
  if hashlib.sha256(motion_restore(name,(ROOT/name).read_bytes())).hexdigest()!=expected:raise ValueError('Unreviewed Signature1278 source: '+name)
 changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 if changed-set(spec['paths'])-motion_paths():raise ValueError('Unreviewed Signature1278 scope: '+str(sorted(changed-set(spec['paths'])-motion_paths())))
 print('PASS: exact incremental Signature1278 sources; physical acceptance remains separate.')
if __name__=='__main__':verify_current()
