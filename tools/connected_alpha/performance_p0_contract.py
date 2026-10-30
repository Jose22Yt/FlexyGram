"""Exact performance-only overlay over PR131; no mutation of historical manifests or signing."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE='0030904ae2e41d7720f43b7906c6a302ed339839'
MANIFEST=ROOT/'tools/performance_p0/review.json'


def spec():return json.loads(MANIFEST.read_text())
def paths():
    from work1_contract import paths as work1_paths
    return frozenset(spec()['paths']) | work1_paths()


@lru_cache(maxsize=256)
def original(path):
    result=subprocess.run(['git','show',BASE+':'+str(path)],cwd=ROOT,capture_output=True)
    return result.stdout if result.returncode==0 else b''


def restore(path,data):
    from work1_contract import restore as work1_restore
    data=work1_restore(path,data)
    expected=spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest()==expected else data


def verify_current():
    from work1_contract import verify_current as verify_work1, restore as work1_restore
    verify_work1()
    current=spec()
    if current['base']!=BASE:raise ValueError('Incorrect performance base')
    for path,expected in current['reviewed'].items():
        file=ROOT/path
        data=work1_restore(path,file.read_bytes() if file.is_file() else b'')
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unreviewed performance source: '+path)
        if restore(path,data+b'\nUNREVIEWED\n')!=data+b'\nUNREVIEWED\n':raise ValueError('Unknown bytes were accepted')
    changed=set(subprocess.check_output(['git','diff','--no-renames',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unknown performance scope: '+repr(sorted(changed-paths())))
