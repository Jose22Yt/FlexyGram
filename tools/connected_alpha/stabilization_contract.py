"""Strict reversible corrective presentation/lifecycle delta on integrated Alpha1271."""
from pathlib import Path
from functools import lru_cache
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='997ac40a65be00c672dc8009b61f55825537d498'
PATHS=frozenset(['.github/workflows/connected-alpha-arm64.yml', '.github/workflows/pr.yml', 'TMessagesProj/build.gradle', 'TMessagesProj/src/main/AndroidManifest.xml', 'TMessagesProj/src/main/java/app/exteraless/player/PlayerMiniView.java', 'TMessagesProj/src/main/java/app/exteraless/player/SignatureMusicBubble.java', 'TMessagesProj/src/main/java/app/exteraless/player/SignatureMusicHost.java', 'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraChatsActivity.java', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubblePreviewView.java', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSettingsActivity.java', 'TMessagesProj/src/main/java/app/flexygram/login/SignatureLoginOutline.java', 'TMessagesProj/src/main/java/app/flexygram/settings/SignatureMatteSettingsActivity.java', 'TMessagesProj/src/main/java/app/flexygram/settings/SignatureNavigationCell.java', 'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java', 'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/FragmentContextView.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/OutlineTextContainerView.java', 'TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java', 'TMessagesProj/src/main/res/values-es/flexygram_bubbles.xml', 'TMessagesProj/src/main/res/values-ru/flexygram_bubbles.xml', 'TMessagesProj/src/main/res/values/flexygram_bubbles.xml', 'tools/connected_alpha/STABILIZATION1272.md', 'tools/connected_alpha/build_private_apk.py', 'tools/connected_alpha/check_source.py', 'tools/connected_alpha/integration_contract.py', 'tools/connected_alpha/login_parity.py', 'tools/connected_alpha/music_visual/MusicVisualTest.java.in', 'tools/connected_alpha/music_visual/reproduce_detach.py', 'tools/connected_alpha/music_visual/stubs.py', 'tools/connected_alpha/release_1270_contract.py', 'tools/connected_alpha/stabilization1272.patch', 'tools/connected_alpha/stabilization_contract.py', 'tools/connected_alpha/test_integrated_release.py', 'tools/connected_alpha/test_preview_navigation.py', 'tools/connected_alpha/test_signature1271.py', 'tools/connected_alpha/test_signature_login.py', 'tools/connected_alpha/test_signature_music.py', 'tools/connected_alpha/test_stabilization1272.py'])
@lru_cache(maxsize=2)
def sections(stamp):
 p=ROOT/'tools/connected_alpha/stabilization1272.patch'
 return {x.split(b'\n',1)[0]:b'diff --git '+x for x in p.read_bytes().split(b'diff --git ')[1:]}
@lru_cache(maxsize=96)
def original(path):
 r=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
 return r.stdout if r.returncode==0 else None
def restore1271(path,data):
 path=str(path);p=ROOT/'tools/connected_alpha/stabilization1272.patch'
 if not p.exists():return data
 section=sections(p.stat().st_mtime_ns).get(('a/'+path+' b/'+path).encode())
 if section is None:return data
 base=original(path)
 if data==base:return data
 with tempfile.TemporaryDirectory()as d:
  target=Path(d)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  r=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=d,capture_output=True)
  if r.returncode or (target.read_bytes() if target.exists() else None)!=base:raise ValueError('Unreviewed corrective delta: '+path)
 return base or b''
