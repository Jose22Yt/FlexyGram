"""Current corrective behavior; historical audits remain strict via exact reversible deltas."""
from pathlib import Path
import re,subprocess,tempfile,unittest
from stabilization_contract import ROOT,BASE,restore1271
class Stabilization1272(unittest.TestCase):
 def test_entire_reviewed_production_delta_restores_exact_integrated_base(self):
  patch=(ROOT/'tools/connected_alpha/stabilization1272.patch').read_bytes()
  paths=[x[6:].decode() for x in patch.splitlines() if x.startswith(b'+++ b/')]
  changed=subprocess.check_output(['git','diff','--name-only',BASE,'8619ba40fbd8fd9d9d898ff307fb0c0716661254','--','TMessagesProj','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py'],cwd=ROOT,text=True).splitlines()
  self.assertEqual(set(paths),set(changed))
  for path in paths:
   current=(ROOT/path).read_bytes();old=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
   self.assertEqual(restore1271(path,current),old.stdout if old.returncode==0 else b'',path)
   if path.endswith('.java') and b'public ' in current:
    with self.assertRaises(ValueError,msg=path):restore1271(path,current.replace(b'public ',b'private ',1))
 def test_authentication_playback_sessions_composer_home_and_message_layout_unchanged(self):
  for prefix in ['TMessagesProj/src/main/java/org/telegram/tgnet','TMessagesProj/jni','TMessagesProj/chaquopy','TMessagesProj/src/main/java/app/flexygram/composer','TMessagesProj/src/main/java/app/flexygram/home']:
   if prefix.endswith(('/composer','/home')):
    before=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',prefix],cwd=ROOT,text=True).splitlines())
    current=set(subprocess.check_output(['git','ls-files','--',prefix],cwd=ROOT,text=True).splitlines())
    expectedNew={'TMessagesProj/src/main/java/app/flexygram/home/SignatureFolderAccent.java'} if prefix.endswith('/home') else set()
    from smart_previews1278_contract import paths as smart_paths, restore as restore_smart
    # Permit ONLY new Smart Previews classes reviewed by the independent
    # exact-blob contract; no arbitrary additions in protected home/composer.
    expectedNew|={p for p in smart_paths() if p.startswith(prefix+'/') and p.endswith('.java')}
    self.assertEqual(current,before|expectedNew)
    for path in expectedNew:
     self.assertEqual(restore1271(path,restore_smart(path,(ROOT/path).read_bytes())),b'')
    for path in before:
     self.assertEqual(restore1271(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
    continue
   self.assertEqual(subprocess.check_output(['git','diff',BASE,'--',prefix],cwd=ROOT),b'',prefix)
  for path in ['org/telegram/ui/LoginActivity.java','org/telegram/ui/IntroActivity.java','org/telegram/ui/ChatActivity.java','org/telegram/ui/Cells/ChatMessageCell.java','org/telegram/messenger/MediaController.java','org/telegram/messenger/MusicPlayerService.java','org/telegram/messenger/UserConfig.java','org/telegram/messenger/MessagesController.java','org/telegram/messenger/SendMessagesHelper.java']:
   path='TMessagesProj/src/main/java/'+path
   from next_alpha_contract import restore_visual
   self.assertEqual(restore_visual(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
 def test_cancelled_spring_rolls_back_and_stale_callback_cannot_close_another_fragment(self):
  source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text();start=source.index('currentSpringAnimation.addEndListener(',source.index('private void animateBackEndAnimation'))
  statement=source[start:source.index('            currentSpringAnimation.start();',start)]
  fixture='''import org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator;public class BackEndProbe {
 interface End {void end(SpringAnimation a,boolean canceled,float v,float speed);}
 static class SpringAnimation {void cancel(){finish(true);}End listener;void addEndListener(End l){listener=l;}void finish(boolean canceled){listener.end(this,canceled,0,0);}}
 FlexyInstantNavigationCoordinator instantNavigation;SpringAnimation currentSpringAnimation;boolean rollback,instantSwipeSettlingClosing,predictiveBackInProgress;int calls,resets;
 void resetPredictiveBackState(){resets++;}
 void onSlideAnimationEnd(boolean b){if(currentSpringAnimation!=null)throw new AssertionError();rollback=b;calls++;}
 void install(boolean backAnimation){boolean instantGestureOwned=false;long instantGestureTicket=0;_STATEMENT_}
 _OBSOLETE_
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] a){
  BackEndProbe p=new BackEndProbe();p.currentSpringAnimation=new SpringAnimation();SpringAnimation first=p.currentSpringAnimation;p.install(false);first.finish(true);check(p.rollback&&p.calls==1&&p.resets==1&&!p.instantSwipeSettlingClosing);first.finish(false);check(p.calls==1);
  p.currentSpringAnimation=new SpringAnimation();SpringAnimation stale=p.currentSpringAnimation;p.install(false);p.currentSpringAnimation=new SpringAnimation();stale.finish(false);check(p.calls==1);p.install(false);p.currentSpringAnimation.finish(false);check(!p.rollback&&p.calls==2&&!p.instantSwipeSettlingClosing);
  p.predictiveBackInProgress=true;p.currentSpringAnimation=new SpringAnimation();p.install(false);check(!p.instantSwipeSettlingClosing);p.currentSpringAnimation.finish(false);check(!p.rollback&&p.calls==3);
  p.predictiveBackInProgress=false;p.currentSpringAnimation=new SpringAnimation();p.install(true);check(!p.instantSwipeSettlingClosing);p.currentSpringAnimation.finish(false);check(p.rollback&&p.calls==4);
 }}'''.replace('_STATEMENT_',statement).replace('_OBSOLETE_',__import__('test_preview_navigation').method(source,'private boolean isObsoleteInstantFrame('))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'BackEndProbe.java';p.write_text(fixture);subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(p),str(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyInstantNavigationCoordinator.java')],check=True);subprocess.run(['java','-cp',d,'BackEndProbe'],check=True)
 def test_current_release_version_increases_without_changing_package(self):
  from next_alpha_contract import restore1272
  source=restore1272('TMessagesProj/build.gradle',(ROOT/'TMessagesProj/build.gradle').read_bytes()).decode();before=subprocess.check_output(['git','show',BASE+':TMessagesProj/build.gradle'],cwd=ROOT,text=True)
  new=int(re.search(r'def verCode = (\d+)',source)[1]);old=int(re.search(r'def verCode = (\d+)',before)[1]);self.assertEqual(new,1272);self.assertGreater(new,old)
  self.assertEqual((ROOT/'gradle.properties').read_bytes(),subprocess.check_output(['git','show',BASE+':gradle.properties'],cwd=ROOT))
