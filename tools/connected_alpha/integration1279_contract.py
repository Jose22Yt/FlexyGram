"""Exact integration review; original PR manifests and historical bytes stay frozen.

Projection is allowed only for a byte-exact reviewed integrated file. Each
independent audit still checks its original snapshot, including unknown-edit
rejection. Behavioral/native tests continue to execute the integrated sources.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE='14e586b4ddb7a686f39cda3cb175920c49cecf11'
MANIFEST=ROOT/'tools/connected_alpha/integration1279_review.json'
PROJECTIONS=ROOT/'tools/connected_alpha/integration1279_projections.json'

# Review additive Instant Navigation P1 only by its exact Git blob, keeping all
# frozen Alpha1279 projections and historical audits intact.
HANDOFF_NAV='TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java'
HANDOFF_NAV_BLOB='590150e5e81b16e45d62b1c5175bc80bee5570a5'
HANDOFF_NAV_BASE_BLOB='78b0b482add965ca590d9da397bc083dd7a5ab3c'
HANDOFF_ADDITIONS={
    'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyNavigationHandoffPolicy.java': '4b8d7d15dc4f1d0db180c572e35bd4393460f66a',
    'tools/connected_alpha/motion/InstantHandoffPolicyTest.java': '4f9a0dd2ebf3700573cae7e0cf8c2bedf8b3fd06',
    'tools/connected_alpha/motion/verify_instant_handoff.py': '8a60708d3d72e6c64cef9426bc56fa7c1c89d1cd',
    'tools/connected_alpha/motion/INSTANT_NAVIGATION_P1.md': '8fc81320f772f2d4effd146f739b72c0e2344709',
    '.github/workflows/instant-navigation-handoff.yml': '8dba73296bb8cae71a4f860d3296b3053a719f02',
}
HANDOFF_CONTRACT='tools/connected_alpha/integration1279_contract.py'

def git_blob_sha(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def restore_handoff(path,data):
    if str(path)==HANDOFF_NAV and git_blob_sha(data)==HANDOFF_NAV_BLOB:
        return blob(HANDOFF_NAV_BASE_BLOB)
    return data

def spec():return json.loads(MANIFEST.read_text())
def paths():return frozenset(spec()['paths']) | frozenset(HANDOFF_ADDITIONS) | frozenset((HANDOFF_CONTRACT,))
def sha(data):return hashlib.sha256(data).hexdigest()

@lru_cache(maxsize=512)
def baseline(path):
    result=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
    return result.stdout if result.returncode==0 else b''

@lru_cache(maxsize=512)
def blob(oid):
    return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)

def project(scope,path,data):
    path=str(path)
    data=restore_handoff(path,data)
    expected=spec()['reviewed'].get(path)
    if expected is None or sha(data)!=expected:return data
    views=json.loads(PROJECTIONS.read_text())
    if views['base']!=BASE:raise ValueError('Incorrect integration projection base')
    oid=views['views'].get(scope,{}).get(path)
    return blob(oid) if oid else baseline(path)

def verify_current():
    s=spec()
    if s['base']!=BASE:raise ValueError('Incorrect Alpha1279 base')
    for path,expected in s['reviewed'].items():
        if sha(restore_handoff(path,(ROOT/path).read_bytes()))!=expected:
            raise ValueError('Unreviewed Alpha1279 integrated source: '+path)
    for path,expected in HANDOFF_ADDITIONS.items():
        if git_blob_sha((ROOT/path).read_bytes())!=expected:
            raise ValueError('Unreviewed Instant Handoff additive source: '+path)
    if git_blob_sha((ROOT/HANDOFF_NAV).read_bytes())!=HANDOFF_NAV_BLOB:
        raise ValueError('Unreviewed Instant Handoff navigation delta')
    changed=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
    if changed-paths():raise ValueError('Unreviewed Alpha1279 scope: '+repr(sorted(changed-paths())))
    print('PASS: exact combined Alpha1279 sources; original PR reviews retained; device acceptance pending.')

if __name__=='__main__':verify_current()
