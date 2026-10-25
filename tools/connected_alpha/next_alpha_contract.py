"""Exact reviewed delta on Alpha1272; reject changes outside the recorded patch."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='8619ba40fbd8fd9d9d898ff307fb0c0716661254'
PATHS=frozenset(['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java','tools/connected_alpha/preview_input1273.patch','tools/connected_alpha/next_alpha_contract.py','tools/connected_alpha/test_preview_input1273.py','tools/connected_alpha/check_source.py','tools/connected_alpha/stabilization_contract.py','tools/connected_alpha/test_stabilization1272.py','tools/connected_alpha/NEXT_ALPHA.md','tools/connected_alpha/preview_visual/run.py','tools/connected_alpha/preview_visual/PreviewInputAndroidTest.java.in','.github/workflows/pr.yml'])
def restore1272(path,data):
 path=str(path)
 data=restore_visual(path,data)
 patch=(ROOT/'tools/connected_alpha/preview_input1273.patch').read_bytes()
 sections={x.split(b'\n',1)[0]:b'diff --git '+x for x in patch.split(b'diff --git ')[1:]}
 section=sections.get(('a/'+path+' b/'+path).encode())
 if section is None:return data
 original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
 if data==original:return data
 with tempfile.TemporaryDirectory()as tmp:
  target=Path(tmp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=tmp,capture_output=True)
  if result.returncode or target.read_bytes()!=original:raise ValueError('Unreviewed next-alpha delta: '+path)
 return original

VISUAL_BASE='43e14d876601d16890b8c6f24c515103e6ece54f'
VISUAL_PATHS=frozenset(['TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubblePreviewView.java', 'TMessagesProj/src/main/res/values/flexygram_bubbles.xml', 'TMessagesProj/src/main/res/values-es/flexygram_bubbles.xml', 'TMessagesProj/src/main/res/values-ru/flexygram_bubbles.xml', 'TMessagesProj/src/main/java/org/telegram/ui/ThemeActivity.java', 'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraChatsActivity.java', 'TMessagesProj/src/main/java/app/flexygram/settings/SignatureChatThemeActivity.java', 'TMessagesProj/src/main/java/app/flexygram/settings/SignatureNativeRowSurface.java', '.github/workflows/pr.yml', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSettingsActivity.java', 'TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java', 'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java', 'TMessagesProj/src/main/java/org/telegram/ui/ChatBackgroundDrawable.java'])
PATHS = PATHS | VISUAL_PATHS | frozenset(['tools/connected_alpha/test_signature_next1273.py','tools/connected_alpha/signature_next1273.patch','tools/connected_alpha/bubble_visual/BubbleVisualTest.java.in','tools/connected_alpha/bubble_visual/BubblePreviewVisualTest.java.in','tools/connected_alpha/bubble_visual/stubs.py','tools/connected_alpha/bubble_visual/run.py'])
def restore_visual(path,data):
 if path not in VISUAL_PATHS:return data
 probe=subprocess.run(['git','show',VISUAL_BASE+':'+path],cwd=ROOT,capture_output=True)
 original=probe.stdout if probe.returncode==0 else None
 if data==original:return data
 patch=(ROOT/'tools/connected_alpha/signature_next1273.patch').read_bytes()
 sections={x.split(b'\n',1)[0]:b'diff --git '+x for x in patch.split(b'diff --git ')[1:]}
 section=sections.get(('a/'+path+' b/'+path).encode())
 if section is None:raise ValueError('Missing reviewed visual delta: '+path)
 with tempfile.TemporaryDirectory()as tmp:
  target=Path(tmp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=tmp,capture_output=True)
  if result.returncode or (target.read_bytes() if target.exists() else None)!=original:raise ValueError('Unreviewed next-alpha visual delta: '+path)
 return original or b''

PATHS = PATHS | frozenset(["tools/connected_alpha/test_theme_sections1273.py","tools/connected_alpha/matte_visual/run.py","tools/connected_alpha/matte_visual/MatteVisualTest.java.in"])

PATHS = PATHS | frozenset(["tools/connected_alpha/bubble_visual/CachedBlurVisualTest.java.in"])

PATHS = PATHS | frozenset(["tools/connected_alpha/test_cached_blur1273.py"])

# Selective PR90 production + its lab; original branch UI remains outside this integration.
from performance.contract import PATHS as PERFORMANCE_PATHS, PRODUCTION as PERFORMANCE_PRODUCTION
VISUAL_PATHS = VISUAL_PATHS | PERFORMANCE_PRODUCTION
PATHS = PATHS | PERFORMANCE_PATHS | PERFORMANCE_PRODUCTION

MUSIC3_PATHS = frozenset(["TMessagesProj/src/main/java/app/exteraless/player/"+n+".java" for n in ("SignatureCoverFade","CoverImage","PlayerSheet","PlayerColors","WavySeekBar","ControlsRow")]) | frozenset(["TMessagesProj/src/main/res/"+v+"/flexygram_music.xml" for v in ("values","values-es","values-ru")])
VISUAL_PATHS = VISUAL_PATHS | MUSIC3_PATHS
PATHS = PATHS | MUSIC3_PATHS
PATHS = PATHS | frozenset(["tools/connected_alpha/test_music3_1273.py","tools/connected_alpha/music_visual/LayoutFixture.java.in"])

HEADER_PATHS = frozenset(["TMessagesProj/src/main/java/app/flexygram/header/"+n+".java" for n in ("HeaderConfig","HeaderGeometry","HeaderSurface","SignatureChatHeader","HeaderPreviewView","HeaderSettingsActivity")]) | frozenset(["TMessagesProj/src/main/java/"+p for p in ("org/telegram/ui/ActionBar/ActionBar.java","org/telegram/ui/Components/ChatAvatarContainer.java","org/telegram/ui/ChatActivity.java","app/exteraless/settings/OpenExteraChatsActivity.java","app/exteraless/settings/OpenExteraAppearanceActivity.java")]) | frozenset(["TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt"]) | frozenset(["TMessagesProj/src/main/res/"+l+"/flexygram_header.xml"for l in ("values","values-es","values-ru")])
VISUAL_PATHS = VISUAL_PATHS | HEADER_PATHS
PATHS = PATHS | HEADER_PATHS | frozenset(["tools/connected_alpha/test_header1273.py"])

PATHS = PATHS | frozenset(["tools/connected_alpha/header_visual/run.py","tools/connected_alpha/header_visual/stubs.py","tools/connected_alpha/header_visual/HeaderVisualTest.java.in"])

from performance.navigation_contract import PATHS as NAVIGATION2_PATHS, PRODUCTION as NAVIGATION2_PRODUCTION
VISUAL_PATHS = VISUAL_PATHS | NAVIGATION2_PRODUCTION
PATHS = PATHS | NAVIGATION2_PATHS | NAVIGATION2_PRODUCTION | frozenset(["tools/connected_alpha/performance/work1_after340.patch"])

# Release metadata is reviewed separately from the immutable Alpha1272 contracts.
RELEASE_PATHS=frozenset(['TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py'])
VISUAL_PATHS = VISUAL_PATHS | RELEASE_PATHS
PATHS = PATHS | RELEASE_PATHS | frozenset(['tools/connected_alpha/test_release1273.py'])
