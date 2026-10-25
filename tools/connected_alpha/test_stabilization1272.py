"""Current corrective behavior; historical audits remain strict via exact reversible deltas."""
from pathlib import Path
import re,subprocess,tempfile,unittest
from stabilization_contract import ROOT,BASE,restore1271
class Stabilization1272(unittest.TestCase):
 def test_entire_reviewed_production_delta_restores_exact_integrated_base(self):
  patch=(ROOT/'tools/connected_alpha/stabilization1272.patch').read_bytes()
  paths=[x[6:].decode() for x in patch.splitlines() if x.startswith(b'+++ b/')]
  changed=subprocess.check_output(['git','diff','--name-only',BASE,'--','TMessagesProj','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py'],cwd=ROOT,text=True).splitlines()
  self.assertEqual(set(paths),set(changed))
  for path in paths:
   current=(ROOT/path).read_bytes();old=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
   self.assertEqual(restore1271(path,current),old.stdout if old.returncode==0 else b'',path)
   if path.endswith('.java') and b'public ' in current:
    with self.assertRaises(ValueError,msg=path):restore1271(path,current.replace(b'public ',b'private ',1))
 def test_authentication_playback_sessions_composer_home_and_message_layout_unchanged(self):
  for prefix in ['TMessagesProj/src/main/java/org/telegram/tgnet','TMessagesProj/jni','TMessagesProj/chaquopy','TMessagesProj/src/main/java/app/flexygram/composer','TMessagesProj/src/main/java/app/flexygram/home']:
   self.assertEqual(subprocess.check_output(['git','diff',BASE,'--',prefix],cwd=ROOT),b'',prefix)
  for path in ['org/telegram/ui/LoginActivity.java','org/telegram/ui/IntroActivity.java','org/telegram/ui/ChatActivity.java','org/telegram/ui/Cells/ChatMessageCell.java','org/telegram/messenger/MediaController.java','org/telegram/messenger/MusicPlayerService.java','org/telegram/messenger/UserConfig.java','org/telegram/messenger/MessagesController.java','org/telegram/messenger/SendMessagesHelper.java']:
   path='TMessagesProj/src/main/java/'+path
   self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
 def test_cancelled_spring_rolls_back_and_stale_callback_cannot_close_another_fragment(self):
  source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text();start=source.index('currentSpringAnimation.addEndListener(',source.index('private void animateBackEndAnimation'))
  statement=source[start:source.index('            currentSpringAnimation.start();',start)]
  fixture='''public class BackEndProbe {
 interface End {void end(SpringAnimation a,boolean canceled,float v,float speed);}
 static class SpringAnimation {End listener;void addEndListener(End l){listener=l;}void finish(boolean canceled){listener.end(this,canceled,0,0);}}
 SpringAnimation currentSpringAnimation;boolean rollback;int calls,resets;
 void resetPredictiveBackState(){resets++;}
 void onSlideAnimationEnd(boolean b){if(currentSpringAnimation!=null)throw new AssertionError();rollback=b;calls++;}
 void install(boolean backAnimation){_STATEMENT_}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] a){
  BackEndProbe p=new BackEndProbe();p.currentSpringAnimation=new SpringAnimation();SpringAnimation first=p.currentSpringAnimation;p.install(false);first.finish(true);check(p.rollback&&p.calls==1&&p.resets==1);first.finish(false);check(p.calls==1);
  p.currentSpringAnimation=new SpringAnimation();SpringAnimation stale=p.currentSpringAnimation;p.install(false);p.currentSpringAnimation=new SpringAnimation();stale.finish(false);check(p.calls==1);p.install(false);p.currentSpringAnimation.finish(false);check(!p.rollback&&p.calls==2);
 }}'''.replace('_STATEMENT_',statement)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'BackEndProbe.java';p.write_text(fixture);subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(p)],check=True);subprocess.run(['java','-cp',d,'BackEndProbe'],check=True)
 def test_current_release_version_increases_without_changing_package(self):
  source=(ROOT/'TMessagesProj/build.gradle').read_text();before=subprocess.check_output(['git','show',BASE+':TMessagesProj/build.gradle'],cwd=ROOT,text=True)
  new=int(re.search(r'def verCode = (\d+)',source)[1]);old=int(re.search(r'def verCode = (\d+)',before)[1]);self.assertEqual(new,1272);self.assertGreater(new,old)
  self.assertEqual((ROOT/'gradle.properties').read_bytes(),subprocess.check_output(['git','show',BASE+':gradle.properties'],cwd=ROOT))
