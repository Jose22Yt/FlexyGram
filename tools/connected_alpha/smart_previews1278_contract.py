"""Post-Alpha1278 Signature Smart Previews isolated exact-blob review.

Keeps all frozen earlier release manifests unchanged. The latest changes are
normalized ONLY when their exact expected blobs match the review manifest.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE="14e586b4ddb7a686f39cda3cb175920c49cecf11"
MANIFEST=ROOT/"tools/connected_alpha/smart_previews1278_review.json"

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

@lru_cache(maxsize=64)
def original(path):
    run=subprocess.run(["git","show",BASE+":"+str(path)],cwd=ROOT,capture_output=True)
    return run.stdout if run.returncode==0 else b""

def paths():
    return frozenset(json.loads(MANIFEST.read_text())["paths"])

def restore(path,data):
    expected=json.loads(MANIFEST.read_text())["reviewed"].get(str(path))
    return original(path) if expected is not None and blob(data)==expected else data

def verify_current():
    info=json.loads(MANIFEST.read_text())
    if info["base"]!=BASE:raise ValueError("Incorrect Alpha1278 source base")
    for name,expected in info["reviewed"].items():
        raw=(ROOT/name).read_bytes()
        if blob(raw)!=expected:
            raise ValueError("Unreviewed Smart Previews change: "+name)
    changed=set(subprocess.check_output(
        ["git","diff",BASE,"--name-only"],cwd=ROOT,text=True).splitlines())
    unexpected=changed-paths()
    if unexpected:raise ValueError("Unreviewed Smart Previews scope: "+str(sorted(unexpected)))
    print("PASS: scoped Signature Smart Previews source review. Physical validation still pending.")

if __name__=="__main__":verify_current()
