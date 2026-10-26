"""Reverse only the reviewed Alpha1275 delta onto the approved Alpha1274 HEAD."""
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881'
PATCH = ROOT / 'tools/connected_alpha/alpha1275.patch'

@lru_cache(maxsize=2)
def sections(stamp):
    chunks = []
    for line in PATCH.read_bytes().splitlines(keepends=True):
        if line.startswith(b'diff --git '):
            chunks.append(bytearray())
        if chunks:
            chunks[-1].extend(line)
    return {bytes(part).split(b'\n', 1)[0][11:]: bytes(part) for part in chunks}

def restore(path, data):
    path = str(path)
    section = sections(PATCH.stat().st_mtime_ns).get(('a/' + path + ' b/' + path).encode())
    if section is None:
        return data
    before = subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT, capture_output=True)
    original = before.stdout if before.returncode == 0 else None
    if data == original:
        return data
    # Historical parity audits may re-enter after a later layer already restored
    # the exact bytes of an earlier approved release.
    for revision in ('751c926d91acd536d96b427af5f34f2fe6bedbc4',
                     '534b30c4edea3dffa0fc726eaec254ed8ebadbc1',
                     '43e14d876601d16890b8c6f24c515103e6ece54f',
                     '8619ba40fbd8fd9d9d898ff307fb0c0716661254',
                     '997ac40a65be00c672dc8009b61f55825537d498',
                     '0e359f0e7841a99d61c79f996dd162b7c836a9bf'):
        accepted = subprocess.run(['git', 'show', revision + ':' + path], cwd=ROOT, capture_output=True)
        if accepted.returncode == 0 and data == accepted.stdout:
            return data
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        applied = subprocess.run(['git', 'apply', '--reverse', '-'], cwd=directory,
                                 input=section, capture_output=True)
        after = target.read_bytes() if target.exists() else None
        if applied.returncode or after != original:
            raise ValueError('Unreviewed Alpha1275 delta: ' + path)
    return original or b''

def paths():
    return frozenset(header[6:].decode() for header in PATCH.read_bytes().splitlines()
                     if header.startswith(b'+++ b/'))
