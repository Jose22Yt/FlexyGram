"""Only this reviewed performance delta; no Work1 production file may change."""
from pathlib import Path
import subprocess,tempfile
BASE='997ac40a65be00c672dc8009b61f55825537d498'
ROOT=Path(__file__).resolve().parents[3]
PRODUCTION=frozenset(['TMessagesProj/src/main/java/app/exteraless/player/LyricsView.java','TMessagesProj/src/main/java/app/exteraless/player/LyricsFill.java'])
PATHS=frozenset(['tools/connected_alpha/performance/.gitignore', '.github/workflows/performance.yml', '.github/workflows/pr.yml', 'TMessagesProj/src/main/java/app/exteraless/player/LyricsFill.java', 'TMessagesProj/src/main/java/app/exteraless/player/LyricsView.java', 'tools/connected_alpha/integration_contract.py', 'tools/connected_alpha/music_visual/run.py', 'tools/connected_alpha/performance/AUDIT.md', 'tools/connected_alpha/performance/README.md', 'tools/connected_alpha/performance/__init__.py', 'tools/connected_alpha/performance/audit.py', 'tools/connected_alpha/performance/capture.py', 'tools/connected_alpha/performance/compare.py', 'tools/connected_alpha/performance/contract.py', 'tools/connected_alpha/performance/findings.json', 'tools/connected_alpha/performance/metrics.py', 'tools/connected_alpha/performance/native/LyricsHarness.java.in', 'tools/connected_alpha/performance/native/PerformanceNativeTest.java.in', 'tools/connected_alpha/performance/native/run.py', 'tools/connected_alpha/performance/native/stubs.py', 'tools/connected_alpha/performance/perfetto.py', 'tools/connected_alpha/performance/presentation.patch', 'tools/connected_alpha/performance/reference_matrix.json', 'tools/connected_alpha/performance/scenarios.py', 'tools/connected_alpha/test_bubbles1270.py', 'tools/connected_alpha/test_matte_release.py', 'tools/connected_alpha/test_performance.py', 'tools/connected_alpha/test_signature_home.py', 'tools/connected_alpha/test_signature_matte.py'])
RESERVED=('ActionBarLayout.java','DialogsActivity.java','MessageDrawable.java','ChatMessageCell.java','LoginActivity.java','FragmentContextView.java','PlayerBarView.java','BubbleSettingsActivity.java','BubbleConfig.java')
def restore(path,data):
 path=str(path)
 patch=(ROOT/'tools/connected_alpha/performance/presentation.patch').read_bytes()
 header=('diff --git a/'+path+' b/'+path+'\n').encode()
 sections=[b'diff --git '+p for p in patch.split(b'diff --git ')[1:]]
 matches=[p for p in sections if p.startswith(header)]
 if not matches:return data
 if len(matches)!=1:raise ValueError('Ambiguous performance reversal')
 with tempfile.TemporaryDirectory() as temp:
  target=Path(temp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=matches[0],cwd=temp,capture_output=True)
  if result.returncode:raise ValueError('Performance delta differs from reviewed patch: '+path)
  return target.read_bytes()

# Independent PR92 descendant: exact inventory and production reversal live separately.
from .navigation_contract import PATHS as NAVIGATION_PATHS
PATHS = PATHS | NAVIGATION_PATHS
