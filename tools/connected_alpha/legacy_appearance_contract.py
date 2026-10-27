"""Byte-exact reviewed removal of conflicting Exteraless Appearance groups.

The Alpha1278 historical manifest remains immutable. This isolated contract
normalizes only the explicitly approved newer delta for earlier audits.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = "14e586b4ddb7a686f39cda3cb175920c49cecf11"
MANIFEST = ROOT / "tools/connected_alpha/legacy_appearance_review.json"


def _blob(data):
    # Git blob identity, including object header (not raw-content SHA-1).
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


@lru_cache(maxsize=32)
def _base(path):
    return subprocess.check_output(["git", "show", BASE + ":" + str(path)], cwd=ROOT)


def paths():
    data = json.loads(MANIFEST.read_text())
    return frozenset(data["paths"])


def restore(path, data):
    from integration1279_contract import project
    data=project("legacy",path,data)
    path = str(path)
    expected = json.loads(MANIFEST.read_text())["reviewed"].get(path)
    if expected is not None and _blob(data) == expected:
        return _base(path)
    return data


def verify_current():
    from integration1279_contract import project,verify_current as verify_integration,paths as integration_paths
    verify_integration()
    data = json.loads(MANIFEST.read_text())
    if data["base"] != BASE:
        raise ValueError("Unexpected approved Alpha1278 base")
    for path, expected in data["reviewed"].items():
        raw = project("legacy",path,(ROOT / path).read_bytes())
        if _blob(raw) != expected:
            raise ValueError("Unreviewed legacy Appearance removal: " + path)
    changed = set(subprocess.check_output(
        ["git", "diff", BASE, "--name-only"], cwd=ROOT, text=True).splitlines())
    extra = changed - paths() - integration_paths()
    if extra:
        raise ValueError("Legacy Appearance change outside reviewed scope: " + repr(sorted(extra)))
    print("PASS: exact scoped Exteraless Appearance retirement; physical UI pending.")
