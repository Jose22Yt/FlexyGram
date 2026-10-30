"""Exact reference-motion overlay on Alpha1288. Source audit only."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='a56b816d1e2166a72cda075d80be8b6e3b1073ca'
MANIFEST=ROOT/'tools/opex_motion/review.json'
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths'])
@lru_cache(maxsize=128)
def original(path):
 p=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
 return p.stdout if p.returncode==0 else b''
def restore(path,data):
 expected=spec()['reviewed'].get(str(path))
 return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data
def verify_current():
 s=spec()
 if s['base']!=BASE:raise ValueError('Wrong motion base')
 for name,expected in s['reviewed'].items():
  file=ROOT/name;data=file.read_bytes() if file.is_file() else b''
  if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed motion bytes: '+name)
  if restore(name,data+b'UNKNOWN')!=data+b'UNKNOWN':raise ValueError('Unknown motion mutation accepted')
 changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
 changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
 if changed-paths():raise ValueError('Unknown motion scope: '+repr(sorted(changed-paths())))
 print('PASS exact reference-motion overlay; physical matching pending')
