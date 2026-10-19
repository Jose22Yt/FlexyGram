"""Explicit P0.4c boundary. Does not regenerate expected hashes during tests."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='ab063041804674861e865364206c0ef27ef1e953'
def reviewed_native_change(path,previous=None):
    rows=json.loads(Path(__file__).with_name('reviewed_changes.json').read_text())['files']
    if path not in rows:return False
    row=rows[path];current=ROOT/path
    old=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
    before=hashlib.sha256(old.stdout).hexdigest() if old.returncode==0 else None
    return current.is_file() and hashlib.sha256(current.read_bytes()).hexdigest()==row['after'] and before==row['before'] and (previous is None or previous in row['previous'])
def assert_native_scope(test):
    paths=subprocess.check_output(['git','diff','--name-only','--ignore-submodules',BASE],cwd=ROOT,text=True).splitlines()
    for path in paths:
        if path.startswith(('docs/security-p04c/','tests/native_compatibility/')):continue
        test.assertTrue(reviewed_native_change(path),path)
