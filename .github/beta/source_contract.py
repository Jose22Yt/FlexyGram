"""Exact infrastructure-only audit overlay over pinned PR150. Never used in the APK build."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '8fbd53ef7847856e52a665d111266de151539f6d'
MANIFEST = ROOT/'.github/beta/review.json'


def spec(): return json.loads(MANIFEST.read_text())
def paths(): return frozenset(spec()['paths'])

@lru_cache(maxsize=64)
def original(path):
    result = subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return result.stdout if result.returncode == 0 else b''


def restore(path, data):
    expected = spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest() == expected else data


def verify_current():
    current = spec()
    if current['base'] != BASE: raise ValueError('Wrong private Beta infrastructure base')
    for name, expected in current['reviewed'].items():
        path = ROOT/name
        data = path.read_bytes() if path.is_file() else b''
        if hashlib.sha256(data).hexdigest() != expected: raise ValueError('Unreviewed infrastructure bytes: '+name)
        if restore(name,data+b'UNKNOWN') != data+b'UNKNOWN': raise ValueError('Unknown bytes accepted')
    changed = set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
    changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
    if changed-paths(): raise ValueError('Unknown infrastructure scope: '+repr(sorted(changed-paths())))
    print('PASS exact private build infrastructure; no private APK or runtime proof')
