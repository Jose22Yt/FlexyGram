"""Exact restoration over Alpha1281. Historic projections never execute old code."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
PIN="a4d66fc84695f59a17a1d30ac888cd18ebcb1bba"
MANIFEST=ROOT/"tools/connected_alpha/native_motion_restore_review.json"
def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()["paths"])
def read_current(path):
    file=ROOT/str(path)
    if file.is_file():return file.read_bytes()
    if spec()["reviewed"].get(str(path))==hashlib.sha256(b"").hexdigest():return b""
    raise FileNotFoundError(file)
@lru_cache(maxsize=256)
def original(path):
    p=subprocess.run(["git","show",PIN+":"+str(path)],cwd=ROOT,capture_output=True)
    return p.stdout if p.returncode==0 else b""
def restore(path,data):
    expected=spec()["reviewed"].get(str(path))
    # Deleted engine files are explicitly reviewed as empty, not exempted.
    if expected and hashlib.sha256(data).hexdigest()==expected:return original(path)
    return data
def verify_current():
    s=spec()
    if s["pin"]!=PIN:raise ValueError("Incorrect restoration base")
    for name,expected in s["reviewed"].items():
        if hashlib.sha256(read_current(name)).hexdigest()!=expected:raise ValueError("Unreviewed native restoration: "+name)
    changed=set(subprocess.check_output(["git","diff",PIN,"--name-only"],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError("Unreviewed restoration scope: "+repr(sorted(changed-paths())))
    print("PASS: exact native restoration; no physical acceptance implied")
if __name__=="__main__":verify_current()
