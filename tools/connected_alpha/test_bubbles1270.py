import hashlib
import subprocess
import unittest
from pathlib import Path
from release_1270_contract import BASE,PATHS
from music_contract import PATHS as MUSIC_PATHS
PATHS = PATHS | MUSIC_PATHS
from bubble_parity import restore_bubble_presentation
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
class BubbleReleaseTests(unittest.TestCase):
 def test_exact_release_scope_and_approved_composer_matte_previews_are_frozen(self):
  changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
  self.assertFalse(changed-PATHS,changed-PATHS)
  for prefix in ('TMessagesProj/src/main/java/app/flexygram/composer','TMessagesProj/src/main/java/app/flexygram/settings','TMessagesProj/src/main/java/app/exteraless/appearance','TMessagesProj/jni','TMessagesProj/chaquopy'):
   self.assertEqual(subprocess.check_output(['git','diff',BASE,'--',prefix],cwd=ROOT),b'',prefix)
 def test_reviewed_native_patch_restores_exact_approved_base(self):
  patch=(ROOT/'tools/connected_alpha/bubble_native_presentation.patch').read_text()
  paths=[line.split(' b/')[1] for line in patch.splitlines() if line.startswith('diff --git ')]
  self.assertEqual(len(paths),6)
  for path in paths:
   actual=(ROOT/path).read_bytes();expected=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
   self.assertEqual(restore_bubble_presentation(path,actual),expected)
   mutation=actual.replace(b'public ',b'private ',1)
   try: restored=restore_bubble_presentation(path,mutation)
   except ValueError: continue
   self.assertNotEqual(restored,expected)
 def test_home2_production_delta_is_exact_work2_without_version_or_workflow_rollback(self):
  for path in ('app/flexygram/home/SignatureHomePainter.java','app/flexygram/home/SignatureHomeStyle.java','app/flexygram/home/SignatureHomeTint.java','org/telegram/ui/Components/FilterTabsView.java'):
   path='TMessagesProj/src/main/java/'+path
   self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','cb2c98234aa7e88550853d54132e52d629b2674f:'+path],cwd=ROOT))
 def test_glass_uses_native_path_shared_wallpaper_and_restores_shared_drawable(self):
  m=(JAVA/'org/telegram/ui/ActionBar/MessageDrawable.java').read_text()
  cell=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
  chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
  self.assertIn('finally { drawable.setFlexyGlassSource(null); }',cell)
  self.assertIn('p.setAlpha(originalAlpha)',m)
  self.assertIn('navbarContentSourceWallpaper.draw(canvas',chat)
  source=chat.split('public boolean drawFlexyBubbleWallpaper')[1].split('@Override')[0]
  for expensive in ('new Bitmap','new Paint','new Path','new Shader','stackBlur','beginRecording','saveLayer'):
   self.assertNotIn(expensive,source)
 def test_saved_radius_and_four_local_controls_preserved(self):
  s=(JAVA/'org/telegram/messenger/SharedConfig.java').read_text()
  self.assertIn('preferences.getInt("bubbleRadius",',s)
  self.assertNotIn('putInt("bubbleRadius", 20)',s)
  settings=(JAVA/'app/flexygram/bubbles/BubbleSettingsActivity.java').read_text()
  self.assertEqual(settings.count(' = addRow("flexyBubble'),4)
  self.assertIn('seek.setMax(100)',settings)
  self.assertNotIn('recreate(',settings)

 def test_actual_cell_glass_callback_compiles_before_late_declared_delegate(self):
  source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
  start=source.index('    private final MessageDrawable.GlassSource flexyBubbleSource =')
  field=source[start:source.index(';',start)+1]
  runner="""class MessageDrawable {interface GlassSource {boolean draw(Object canvas,Object path);}}
class CallbackProbe {
_FIELD_
 interface Delegate {boolean drawFlexyBubbleWallpaper(Object cell,Object canvas,Object path);}
 Delegate delegate=(a,b,c)->true;boolean drawForBlur;
 public static void main(String[] args){CallbackProbe p=new CallbackProbe();if(!p.flexyBubbleSource.draw(null,null))throw new AssertionError();p.drawForBlur=true;if(p.flexyBubbleSource.draw(null,null))throw new AssertionError();}
}""".replace('_FIELD_',field)
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'CallbackProbe.java';p.write_text(runner)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(p)],check=True)
   subprocess.run(['java','-cp',temp,'CallbackProbe'],check=True)
