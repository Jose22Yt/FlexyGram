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
