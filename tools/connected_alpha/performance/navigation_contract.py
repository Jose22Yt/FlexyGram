"""Exact Performance2 boundary on PR92. No reserved production mutation permitted."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[3]
BASE='340cd323f5f5809abc746507b2e252da71298720'
ALPHA1272='8619ba40fbd8fd9d9d898ff307fb0c0716661254'
PRODUCTION=frozenset(['TMessagesProj/src/main/java/org/telegram/messenger/ImageReceiver.java'])
PATHS=frozenset([
 *PRODUCTION,
 '.github/workflows/performance2.yml','.github/workflows/pr.yml',
 'tools/connected_alpha/test_performance2.py','tools/connected_alpha/next_alpha_contract.py',
 *('tools/connected_alpha/performance/'+p for p in [
  'capture.py','compare.py','contract.py','perfetto.py','navigation.py','navigation_contract.py',
  'radius_probe.py','ci.patch','radius.patch','navigation_audit.py','NAVIGATION2.md','reference_navigation2.json',
  'native/RadiusProbe.java.in','native/PerformanceNativeTest.java.in','native/stubs.py'])])
RESERVED_NAMES=frozenset(['ActionBarLayout.java','DialogsActivity.java','ChatActivity.java','MessageDrawable.java',
 'ChatMessageCell.java','ChatBackgroundDrawable.java','FragmentContextView.java','PlayerBarView.java','PlayerSheet.java',
 'SignatureMusicBubble.java','SignatureMusicHost.java','BubbleConfig.java','BubbleSettingsActivity.java'])

def reserved():
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','TMessagesProj'],cwd=ROOT,text=True).splitlines()
    work1=set(subprocess.check_output(['git','diff','--name-only',ALPHA1272,BASE,'--','TMessagesProj'],cwd=ROOT,text=True).splitlines())
    return sorted(work1|{p for p in tracked if Path(p).name in RESERVED_NAMES or '/app/flexygram/home/' in p or '/app/exteraless/player/' in p or '/app/flexygram/composer/' in p})

def reverse(data):
    path=next(iter(PRODUCTION))
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
        result=subprocess.run(['git','apply','--reverse','-'],input=(ROOT/'tools/connected_alpha/performance/radius.patch').read_bytes(),cwd=temp,capture_output=True)
        before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        if result.returncode or target.read_bytes()!=before:raise ValueError('Unreviewed ImageReceiver delta')
        return before


def restore_ci(data):
    path='.github/workflows/pr.yml'
    marker=b"github.head_ref != 'perf/alpha1273-engineering2' && "
    if marker not in data:return data
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
        result=subprocess.run(['git','apply','--reverse','-'],input=(ROOT/'tools/connected_alpha/performance/ci.patch').read_bytes(),cwd=temp,capture_output=True)
        before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        if result.returncode or target.read_bytes()!=before:raise ValueError('Unreviewed Performance2 CI delta')
        return before

# Integration boundary: Work1 UI commits after the original PR93 base are reversed exactly,
# independently from PR93's tiny ImageReceiver patch. Never rewrite the four-cohort baseline.
PATHS = PATHS | frozenset(['tools/connected_alpha/performance/work1_after340.patch'])
def work1_paths():
    patch=(ROOT/'tools/connected_alpha/performance/work1_after340.patch').read_bytes()
    return frozenset(line[6:].decode() for line in patch.splitlines() if line.startswith(b'+++ b/'))
def restore_reserved(path,data):
    from studio_contract import restore as restore_studio
    data=restore_studio(path,data) if any(marker in data for marker in (b"FlexyStudio",b"FlexyStyleInstallHelper",b"flexystudio")) else data
    patch=(ROOT/'tools/connected_alpha/performance/work1_after340.patch').read_bytes()
    sections={part.split(b'\n',1)[0]:b'diff --git '+part for part in patch.split(b'diff --git ')[1:]}
    section=sections.get(('a/'+path+' b/'+path).encode())
    if section is None:return data
    result=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
    expected=result.stdout if result.returncode==0 else None
    with tempfile.TemporaryDirectory()as temp:
        target=Path(temp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
        applied=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=temp,capture_output=True)
        if applied.returncode or (target.read_bytes() if target.exists() else None)!=expected:raise ValueError('Unreviewed integrated Work1 delta: '+path)
    return expected or b''
def validate_work1():
    paths=work1_paths()
    for path in paths:restore_reserved(path,(ROOT/path).read_bytes())
    return paths
