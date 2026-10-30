"""Exact P0 performance overlay on PR136. Source-audit projection only; never runtime code."""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = 'cd2af16c8271e52738f0c4e726cf59862c637087'
MANIFEST = ROOT / 'tools/deep_performance/review.json'


def spec():
    return json.loads(MANIFEST.read_text())


def paths():
    from beta_integration_contract import paths as latest_paths
    return frozenset(spec()['paths']) | latest_paths()


@lru_cache(maxsize=128)
def original(path):
    result = subprocess.run(['git', 'show', BASE + ':' + str(path)], cwd=ROOT, capture_output=True)
    return result.stdout if result.returncode == 0 else b''


def restore(path, data):
    from beta_integration_contract import restore as latest_restore
    data = latest_restore(path,data)
    expected = spec()['reviewed'].get(str(path))
    return original(path) if expected and hashlib.sha256(data).hexdigest() == expected else data


def verify_current():
    from beta_integration_contract import verify_current as latest_verify, restore as latest_restore
    latest_verify()
    current = spec()
    if current['base'] != BASE:
        raise ValueError('Wrong deep-performance base')
    for name, expected in current['reviewed'].items():
        file = ROOT / name
        data = latest_restore(name,file.read_bytes() if file.is_file() else b'')
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Unreviewed deep-performance bytes: ' + name)
        if restore(name, data + b'UNKNOWN') != data + b'UNKNOWN':
            raise ValueError('Unknown mutation accepted: ' + name)
    changed = set(subprocess.check_output(['git', 'diff', '--no-renames', BASE, '--name-only'], cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines())
    if changed - paths():
        raise ValueError('Unknown deep-performance scope: ' + repr(sorted(changed - paths())))
    print('PASS exact deep-performance delta; device acceptance remains separate')


if __name__ == '__main__':
    verify_current()
