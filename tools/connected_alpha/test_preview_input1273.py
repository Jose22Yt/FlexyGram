"""Execute native tab visibility and owner callback bodies with explicit UI doubles.

No Android device, private chat, graphics benchmark or physical acceptance is implied.
The old sequence leaves a clickable alpha-zero overlay after a preview with no frame.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = '8619ba40fbd8fd9d9d898ff307fb0c0716661254'
JAVA = ROOT/'TMessagesProj/src/main/java/org/telegram/ui'


def body(source, anchor):
    start = source.index(anchor)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end].replace('@NonNull ', '')


def fixture(dialogs):
    pager = (JAVA/'ViewPagerActivity.java').read_text()
    tabs = (JAVA/'MainTabsActivity.java').read_text()
    state = body(pager, 'protected static class FragmentState')
    owner = body(tabs, 'public void onBecomeFullyVisible()')
    callback = ''
    if 'public void onParentBecomeFullyVisible()' in dialogs:
        callback = body(dialogs, 'public void onParentBecomeFullyVisible()')
        callback += body(dialogs, 'private void clearClosedPreviewOverlay()')
    return r'''
public class PreviewInputRegression {
 static class View {
  static final int VISIBLE=0,GONE=8; int visibility=VISIBLE;float alpha;Object background=new Object();
  int getVisibility(){return visibility;} void setVisibility(int v){visibility=v;}
  void setBackground(Object b){background=b;}void setAlpha(float a){alpha=a;}
  boolean consumesTap(){return visibility==VISIBLE;} // explicit clickable Android view double, even at alpha zero
 }
 static class BaseFragment {
  Object fragmentView=new Object();int ends;
  void onResume(){}void onPause(){}void onBecomeFullyVisible(){}void onBecomeFullyHidden(){}
  void onTransitionAnimationStart(boolean o,boolean b){}
  void onTransitionAnimationProgress(boolean o,float p){}
  void onTransitionAnimationEnd(boolean o,boolean b){ends++;}
 }
 interface TabFragmentDelegate{default void onParentBecomeFullyVisible(){}}
 static class Layout {boolean preview,transition;
  boolean isInPreviewMode(){return preview;}boolean isTransitionAnimationInProgress(){return transition;}}
 static class Dialogs extends BaseFragment implements TabFragmentDelegate {
  Layout parentLayout=new Layout();View blurredView=new View();int updates;
  void checkUi_mainTabsVisible(){updates++;}
  CALLBACK
 }
 static class Tabs extends BaseFragment {
  BaseFragment selected; BaseFragment getCurrentVisibleFragment(){return selected;}
  OWNER
 }
 STATE
 static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
 public static void main(String[] args){
  boolean old=args.length>0;
  for(int n=0;n<2000;n++){
   Dialogs d=new Dialogs();Tabs tabs=new Tabs();tabs.selected=d;
   FragmentState s=new FragmentState(d);
   s.setVisibility(1,1,true,true); // home already fully visible before opening
   d.blurredView.setVisibility(View.VISIBLE);d.blurredView.setAlpha(0);
   // Both springs completed/canceled before delivering a fractional child visibility.
   // This also occurs when a forced completion jumps from 1 directly back to 1.
   s.setVisibility(1,1,true,true);
   check(d.ends==0,"sequence unexpectedly produced a child transition-end");
   tabs.onBecomeFullyVisible();
   check(d.blurredView.consumesTap()==old,"overlay ownership after return");
   if(!old){
    check(d.blurredView.background==null,"wallpaper reference leaked");
    d.onParentBecomeFullyVisible();check(d.updates==1,"cleanup not idempotent");
    d.blurredView.setVisibility(View.VISIBLE);d.parentLayout.preview=true;
    tabs.onBecomeFullyVisible();check(d.blurredView.consumesTap(),"active preview removed");
    d.parentLayout.preview=false;d.parentLayout.transition=true;
    tabs.onBecomeFullyVisible();check(d.blurredView.consumesTap(),"active transition removed");
    d.parentLayout.transition=false;tabs.onBecomeFullyVisible();
    check(!d.blurredView.consumesTap(),"interrupted transition return blocked");
    d.parentLayout=null;tabs.onBecomeFullyVisible();
   }
  }
 }
}
'''.replace('CALLBACK',callback).replace('OWNER',owner).replace('STATE',state)


class PreviewInput(unittest.TestCase):
    def test_reviewed_delta_restores1272_and_rejects_unreviewed_changes(self):
        from next_alpha_contract import restore1272
        path='TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java'
        current=(ROOT/path).read_bytes()
        self.assertEqual(restore1272(path,current), subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
        with self.assertRaises(ValueError):
            restore1272(path,current.replace(b'public boolean showChatPreview',b'private boolean showChatPreview',1))

    def test_native_tab_owner_clears_invisible_clickable_overlay_on_zero_frame_return(self):
        path='TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java'
        original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        for source,args in [(original,['original']),((ROOT/path).read_text(),[])]:
            with tempfile.TemporaryDirectory() as tmp:
                java=Path(tmp)/'PreviewInputRegression.java'
                java.write_text(fixture(source))
                subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(java)],check=True)
                subprocess.run(['java','-cp',tmp,'PreviewInputRegression',*args],check=True)
