"""Exact corrective delta layered over PR94; historical contracts still reverse to their original bases."""
from pathlib import Path
from functools import lru_cache
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='534b30c4edea3dffa0fc726eaec254ed8ebadbc1'
PATCH=ROOT/'tools/connected_alpha/refinement1274.patch'
@lru_cache(maxsize=2)
def sections(stamp):
 return {part.split(b'\n',1)[0]:b'diff --git '+part for part in PATCH.read_bytes().split(b'diff --git ')[1:]}
def restore(path,data):
 path=str(path)
 section=sections(PATCH.stat().st_mtime_ns).get(('a/'+path+' b/'+path).encode())
 if section is None:return data
 before=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
 original=before.stdout if before.returncode==0 else None
 if data==original:return data
 with tempfile.TemporaryDirectory()as d:
  target=Path(d)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=d,capture_output=True)
  if result.returncode or (target.read_bytes() if target.exists() else None)!=original:raise ValueError('Unreviewed Alpha1274 delta: '+path)
 return original or b''
PATHS=frozenset(['tools/connected_alpha/refinement1274_contract.py','tools/connected_alpha/refinement1274.patch','tools/connected_alpha/test_refinement1274.py','.github/workflows/refinement1274.yml'])
