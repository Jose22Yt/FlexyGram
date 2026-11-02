"""Exact three-mission overlay over validated PR132. Audit projections never run in Android."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='3db6f7a87d147b84a628af7352299173424ce4f7'
MANIFEST=ROOT/'tools/work1/review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():
 from refinement134_contract import paths as refinement_paths
 return frozenset(spec()['paths']) | refinement_paths()
@lru_cache(maxsize=256)
def original(path):
 r=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
 return r.stdout if r.returncode==0 else b''
def restore(path,data):
 from refinement134_contract import restore as refinement_restore
 data=refinement_restore(path,data)
 expected=spec()['reviewed'].get(str(path))
 return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
 from refinement134_contract import verify_current as verify_refinement, restore as refinement_restore
 verify_refinement()
 s=spec()
 if s['base']!=BASE:raise ValueError('Wrong Work1 base')
 for path,expected in s['reviewed'].items():
  p=ROOT/path;data=refinement_restore(path,p.read_bytes() if p.is_file() else b'')
  if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed Work1 delta: '+path)
  if restore(path,data+b'UNREVIEWED')!=data+b'UNREVIEWED':raise ValueError('Unknown mutation accepted')
 changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
 if changed-paths():raise ValueError('Unknown Work1 scope: '+repr(sorted(changed-paths())))
 print('PASS exact three-mission overlay on PR132; physical acceptance remains separate')
if __name__=='__main__':verify_current()
