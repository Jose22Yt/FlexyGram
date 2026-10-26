"""Exact continuation delta on Work1's saved checkpoint; no broad source exclusions."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='f11921c651b52b080899f9e86a7a975dab0afeb7'
MANIFEST=ROOT/'tools/connected_alpha/files_completion.json'
@lru_cache(maxsize=256)
def original(revision,path):
 r=subprocess.run(['git','show',revision+':'+path],cwd=ROOT,capture_output=True)
 return r.stdout if r.returncode==0 else None

def restore(path,data):
 path=str(path);spec=json.loads(MANIFEST.read_text());digest=spec['existing'].get(path)
 if digest is None:return data
 before=original(BASE,path)
 if hashlib.sha256(data).hexdigest()==digest:return before or b''
 for revision in (BASE,'8c47e5532a600f9a8b4ccbfdac5090d09a1075a0','8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881','534b30c4edea3dffa0fc726eaec254ed8ebadbc1','751c926d91acd536d96b427af5f34f2fe6bedbc4','43e14d876601d16890b8c6f24c515103e6ece54f','8619ba40fbd8fd9d9d898ff307fb0c0716661254','997ac40a65be00c672dc8009b61f55825537d498','0e359f0e7841a99d61c79f996dd162b7c836a9bf'):
  if data==original(revision,path):return data
 raise ValueError('Unreviewed FlexyFiles continuation delta: '+path)

def paths():return frozenset(json.loads(MANIFEST.read_text())['paths'])
