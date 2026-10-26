"""Exact corrective delta layered over PR94; historical contracts still reverse to their original bases."""
from pathlib import Path
from functools import lru_cache
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='534b30c4edea3dffa0fc726eaec254ed8ebadbc1'
PATCH=ROOT/'tools/connected_alpha/refinement1274.patch'
@lru_cache(maxsize=2)
def sections(stamp):
 return {part.split(b'\n',1)[0]:b'diff --git '+part for part in PATCH.read_bytes().split(b'diff --git ')[1:]}
def restore(path,data):
 path=str(path)
 from alpha1275_contract import restore as restore_alpha1275
 data=restore_alpha1275(path,data)
 section=sections(PATCH.stat().st_mtime_ns).get(('a/'+path+' b/'+path).encode())
 if section is None:return data
 before=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
 original=before.stdout if before.returncode==0 else None
 if original is None:
  expected=b'\n'.join(line[1:] for line in section.splitlines() if line.startswith(b'+') and not line.startswith(b'+++'))+b'\n'
  if data!=expected:raise ValueError('Unreviewed Alpha1274 addition: '+path)
  return b''
 if data==original:return data
 # Historical audits re-enter after earlier layers have already restored exact base bytes.
 # Only fixed, approved revisions qualify for this idempotent pass-through.
 for revision in ['751c926d91acd536d96b427af5f34f2fe6bedbc4','43e14d876601d16890b8c6f24c515103e6ece54f','8619ba40fbd8fd9d9d898ff307fb0c0716661254','997ac40a65be00c672dc8009b61f55825537d498','0e359f0e7841a99d61c79f996dd162b7c836a9bf']:
  accepted=subprocess.run(['git','show',revision+':'+path],cwd=ROOT,capture_output=True)
  if accepted.returncode==0 and data==accepted.stdout:return data
 with tempfile.TemporaryDirectory()as d:
  target=Path(d)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=d,capture_output=True)
  if result.returncode or (target.read_bytes() if target.exists() else None)!=original:raise ValueError('Unreviewed Alpha1274 delta: '+path)
 return original or b''
PATHS=frozenset(['tools/connected_alpha/refinement1274_contract.py','tools/connected_alpha/refinement1274.patch','tools/connected_alpha/test_refinement1274.py','tools/connected_alpha/test_integration.py','tools/connected_alpha/REFINEMENT1274.md','.github/workflows/refinement1274.yml'])

PRODUCTION=frozenset(["TMessagesProj/build.gradle","TMessagesProj/src/main/AndroidManifest.xml","TMessagesProj/src/main/java/app/exteraless/player/PlayerColors.java","TMessagesProj/src/main/java/app/exteraless/player/PlayerSheet.java","TMessagesProj/src/main/java/app/exteraless/player/SignatureCoverFade.java","TMessagesProj/src/main/java/app/exteraless/player/SignatureMusicActions.java","TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java","TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleOutline.java","TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSettingsActivity.java","TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java","TMessagesProj/src/main/java/app/flexygram/header/HeaderConfig.java","TMessagesProj/src/main/java/app/flexygram/header/HeaderGeometry.java","TMessagesProj/src/main/java/app/flexygram/header/HeaderPreviewView.java","TMessagesProj/src/main/java/app/flexygram/header/HeaderSettingsActivity.java","TMessagesProj/src/main/java/app/flexygram/header/HeaderSurface.java","TMessagesProj/src/main/java/app/flexygram/header/SignatureChatHeader.java","TMessagesProj/src/main/java/app/flexygram/icons/SignatureLauncherUpdateReceiver.java","TMessagesProj/src/main/java/app/flexygram/studio/core/StudioCodec.java","TMessagesProj/src/main/java/app/flexygram/studio/core/StudioSchema.java","TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java","TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java","TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java","TMessagesProj/src/main/java/org/telegram/ui/Components/ChatAvatarContainer.java","TMessagesProj/src/main/java/org/telegram/ui/Components/SizeNotifierFrameLayout.java","TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java","TMessagesProj/src/main/res/values-es/flexygram_bubbles.xml","TMessagesProj/src/main/res/values-es/flexygram_header.xml","TMessagesProj/src/main/res/values-es/flexygram_music.xml","TMessagesProj/src/main/res/values-ru/flexygram_bubbles.xml","TMessagesProj/src/main/res/values-ru/flexygram_header.xml","TMessagesProj/src/main/res/values-ru/flexygram_music.xml","TMessagesProj/src/main/res/values/flexygram_bubbles.xml","TMessagesProj/src/main/res/values/flexygram_header.xml","TMessagesProj/src/main/res/values/flexygram_music.xml"])
PATHS = PATHS | PRODUCTION

from alpha1275_contract import paths as alpha1275_paths
PATHS = PATHS | alpha1275_paths() | frozenset(['tools/connected_alpha/alpha1275_contract.py','tools/connected_alpha/alpha1275.patch'])
PATHS = PATHS | frozenset(['tools/connected_alpha/signature_refinement_contract.py',
                         'tools/connected_alpha/test_signature_refinement.py'])

PRODUCTION = PRODUCTION | frozenset(['TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureBorderPath.java'])
PATHS = PATHS | PRODUCTION

PRODUCTION = PRODUCTION | frozenset(['TMessagesProj/src/main/java/app/flexygram/preview/SignatureWallpaperPreview.java'])
PATHS = PATHS | PRODUCTION
PRODUCTION = PRODUCTION | frozenset(['TMessagesProj/src/main/java/app/flexygram/composer/FlexyComposerSettingsActivity.java'])
PATHS = PATHS | PRODUCTION | frozenset(['tools/connected_alpha/test_flexy_composer.py',
                                      'tools/connected_alpha/test_stabilization1272.py'])
