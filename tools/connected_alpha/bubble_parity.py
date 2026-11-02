"""Reverse only the explicit reviewed native bubble presentation patch."""
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def restore_bubble_presentation(path, actual):
    from release_1271_contract import restore1270
    actual = restore1270(path, actual)
    patch = (ROOT/'tools/connected_alpha/bubble_native_presentation.patch').read_bytes()
    prefix = ('diff --git a/' + path + ' b/' + path + '\n').encode()
    sections = [b'diff --git ' + p for p in patch.split(b'diff --git ')[1:]]
    match = [p for p in sections if p.startswith(prefix)]
    if len(match) != 1: raise ValueError('Exactly one reviewed presentation patch required: ' + path)
    with tempfile.TemporaryDirectory(prefix='bubble-parity-') as directory:
        target = Path(directory)/path; target.parent.mkdir(parents=True); target.write_bytes(actual)
        result = subprocess.run(['git','apply','--reverse','-'], cwd=directory, input=match[0], capture_output=True)
        if result.returncode: raise ValueError('Native bubble presentation differs from reviewed patch: ' + path)
        return target.read_bytes()
