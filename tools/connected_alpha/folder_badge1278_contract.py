"""A reversible, byte-exact review of the isolated Signature folder palette fix.

Frozen Alpha1278/Alpha1277 audit fingerprints are not rewritten. New code
is normalized only when the exact approved blob hash matches this manifest.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE="14e586b4ddb7a686f39cda3cb175920c49cecf11"
MANIFEST=ROOT/"tools/connected_alpha/folder_badge1278_review.json"

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

@lru_cache(maxsize=64)
def original(path):
    return subprocess.check_output(["git","show",BASE+":"+str(path)],cwd=ROOT)

def paths():
    return frozenset(json.loads(MANIFEST.read_text())["paths"])

def restore(path,data):
    from integration1279_contract import project
    data=project("folders",path,data)
    expected=json.loads(MANIFEST.read_text())["reviewed"].get(str(path))
    return original(path) if expected is not None and blob(data)==expected else data

def verify_current():
    from integration1279_contract import project,verify_current as verify_integration,paths as integration_paths
    verify_integration()
    spec=json.loads(MANIFEST.read_text())
    if spec["base"]!=BASE:raise ValueError("Unexpected base for folder badge fix")
    for name,expected in spec["reviewed"].items():
        actual=project("folders",name,(ROOT/name).read_bytes())
        if blob(actual)!=expected:raise ValueError("Unreviewed Signature folder fix: "+name)
    changed=set(subprocess.check_output(["git","diff",BASE,"--name-only"],cwd=ROOT,text=True).splitlines())
    if changed-paths()-integration_paths():raise ValueError("Unreviewed Signature folder scope: "+str(sorted(changed-paths())))
    print("PASS: reviewed folder badge code and tests; runtime acceptance pending.")

if __name__=="__main__":verify_current()
