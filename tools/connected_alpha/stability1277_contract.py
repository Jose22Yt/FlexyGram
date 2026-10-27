"""Exact corrective delta over the physically reviewed Alpha1276; historical audits remain intact."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='38e677d60847e117ede1c25731f7b6c4fd2970e2'
MANIFEST=ROOT/'tools/connected_alpha/stability1277_review.json'
@lru_cache(maxsize=256)
def original(path):
    r=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return r.stdout if r.returncode==0 else b''
def restore(path,data):
    expected=json.loads(MANIFEST.read_text())['reviewed'].get(str(path))
    if expected is not None and hashlib.sha256(data).hexdigest()==expected:
        return original(path)
    # Older immutable audits handle their own historical inputs and reject unknown bytes.
    return data
def paths():
    return frozenset(json.loads(MANIFEST.read_text())['paths'])
