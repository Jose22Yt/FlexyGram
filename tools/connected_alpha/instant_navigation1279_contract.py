"""Exact-byte additive Instant Navigation P1 projection over signed Alpha1279.

Historical manifests/reviewed source bytes remain frozen. Only files with a
matching recorded Git blob SHA are projected to the signed Alpha1279 snapshot.
All nonmatching/unreviewed edits fail closed in the historical verifiers.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PIN = "d50677f723292d0e405eae8e1529f65416ff9cbd"
MANIFEST = ROOT / "tools/connected_alpha/instant_navigation1279_review.json"


def blob_sha(data):
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def spec():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def paths():
    return frozenset(spec()["paths"])


@lru_cache(maxsize=32)
def original(path):
    process = subprocess.run(
        ["git", "show", PIN + ":" + str(path)],
        cwd=ROOT, capture_output=True, check=False
    )
    return process.stdout if process.returncode == 0 else b""


def restore(path, data):
    name = str(path)
    accepted = spec()["reviewed"].get(name)
    if accepted is None or blob_sha(data) != accepted:
        return data
    return original(name)


def verify_current():
    manifest = spec()
    if manifest["pin"] != PIN:
        raise ValueError("Unexpected Instant Navigation Alpha1279 base")
    for name, expected in manifest["reviewed"].items():
        actual = blob_sha((ROOT / name).read_bytes())
        if actual != expected:
            raise ValueError("Unreviewed Instant Navigation source: " + name)
    changed = set(subprocess.check_output(
        ["git", "diff", PIN, "--name-only"], cwd=ROOT, text=True
    ).splitlines())
    unknown = changed - paths()
    if unknown:
        raise ValueError("Unreviewed Instant Navigation scope: " + repr(sorted(unknown)))
    print("PASS: exact post-1279 handoff overlay; signed base reviews preserved")


if __name__ == "__main__":
    verify_current()
