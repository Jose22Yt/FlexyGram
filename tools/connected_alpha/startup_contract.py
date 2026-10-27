"""Exact, reversible Ultra-Smooth mission delta on the validated PR100 application.
Historical release audits still run against their byte-exact original sources.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='175b299e0d4faeb246eca8e1be16a362a3a62213'
MANIFEST=ROOT/'tools/connected_alpha/startup_review.json'
@lru_cache(maxsize=256)
def original(revision,path):
 result=subprocess.run(['git','show',revision+':'+path],cwd=ROOT,capture_output=True)
 return result.stdout if result.returncode==0 else None

def restore(path,data):
 from stability1277_contract import restore as restore_stability
 data=restore_stability(path,data)
 spec=json.loads(MANIFEST.read_text());path=str(path)
 expected=spec['reviewed'].get(path)
 if expected is None:return data
 before=original(BASE,path)
 if hashlib.sha256(data).hexdigest()==expected:return before or b''
 if before is None and data==b'':return data
 for revision in (BASE,'f11921c651b52b080899f9e86a7a975dab0afeb7','8c47e5532a600f9a8b4ccbfdac5090d09a1075a0','8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881','534b30c4edea3dffa0fc726eaec254ed8ebadbc1','751c926d91acd536d96b427af5f34f2fe6bedbc4','43e14d876601d16890b8c6f24c515103e6ece54f','8619ba40fbd8fd9d9d898ff307fb0c0716661254','997ac40a65be00c672dc8009b61f55825537d498','0e359f0e7841a99d61c79f996dd162b7c836a9bf'):
  historical=original(revision,path)
  # Older exact audits re-enter with an empty result for a file added after their base.
  # The current-checkpoint audit separately requires the nonempty PR100 bytes.
  if data==historical or historical is None and data==b'':return data
 raise ValueError('Unreviewed startup delta: '+path)

def paths():return frozenset(json.loads(MANIFEST.read_text())['paths'])

from stability1277_contract import paths as stability_paths
_original_paths=paths
def paths():return _original_paths() | stability_paths()
