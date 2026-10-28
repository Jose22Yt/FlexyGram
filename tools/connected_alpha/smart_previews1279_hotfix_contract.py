"""Isolated byte-exact hotfix projection over the signed Alpha1279 source.

PIN represents the user's tested Alpha1279 integration snapshot. This
contract must never silently accept arbitrary changes to reviewed files.
Historical PR112 reviews remain unmodified; only precisely reviewed hotfix
blobs project back onto the original compiled release for old audits.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2]
PIN="d50677f723292d0e405eae8e1529f65416ff9cbd"
MANIFEST=ROOT/"tools/connected_alpha/smart_previews1279_hotfix_review.json"

def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def spec():
    return json.loads(MANIFEST.read_text())

def paths():
    from alpha1280_contract import paths as new_paths
    return frozenset(spec()["paths"])|new_paths()

@lru_cache(maxsize=64)
def original(path):
    proc=subprocess.run(["git","show",PIN+":"+str(path)],cwd=ROOT,capture_output=True,check=False)
    return proc.stdout if proc.returncode==0 else b""

def restore(path,data):
    from alpha1280_contract import restore as latest_restore
    data=latest_restore(path,data)
    name=str(path)
    accepted=spec()["reviewed"].get(name)
    return original(name) if accepted and blob_sha(data)==accepted else data

def verify_current():
    from alpha1280_contract import verify_current as verify_latest, restore as latest_restore
    verify_latest()
    data=spec()
    if data["pin"]!=PIN:raise ValueError("Unexpected Alpha1279 pin")
    for name,expected in data["reviewed"].items():
        raw=(ROOT/name).read_bytes()
        if blob_sha(latest_restore(name,raw))!=expected:raise ValueError("Unreviewed Smart Preview hotfix change: "+name)
    changed=set(subprocess.check_output(
        ["git","diff",PIN,"--name-only"],cwd=ROOT,text=True).splitlines())
    unknown=changed-paths()
    if unknown:raise ValueError("Unexpected files in Smart Preview hotfix: "+repr(sorted(unknown)))
    print("PASS: exact Smart Preview Alpha1279 hotfix; physical APK test pending.")

if __name__=="__main__":
    verify_current()
