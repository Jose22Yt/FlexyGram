"""Execute actual native navigation entry/transition bodies with explicit view/fragment doubles.

Reproduces a source-level double-close bug, not the owner's physical ANR.
The old checkTransitionAnimation can remove the preview before its caller chooses
which fragment to close. A second release/back then begins closing Home.
"""
import subprocess,tempfile,unittest
from stabilization_contract import restore1271
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PATH='TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java'
BASE='0e359f0e7841a99d61c79f996dd162b7c836a9bf'
def method(source,anchor):
 a=source.index(anchor);o=source.index('{',a);depth=1;b=o+1
 while depth:
  depth+=(source[b]=='{')-(source[b]=='}');b+=1
 return source[a:b].replace('@Override','')
def fixture(source):
 bodies=[method(source,x) for x in ['public boolean checkTransitionAnimation()', 'public void finishPreviewFragment()', 'public void onBackPressed()', 'private void onCloseAnimationEnd()', 'private void onOpenAnimationEnd()', 'private void onAnimationEndCheck(boolean byCheck)']]
 if 'private void reportInstantNavigation(' in source:bodies+=[method(source,'private void reportInstantNavigation('),method(source,'private boolean isObsoleteInstantCompletion(')]
 if 'private boolean isObsoleteInstantCompletion(' in source:
  a=source.index('            currentSpringAnimation.addEndListener(',source.index('    private void startLayoutAnimation('));b=source.index('            currentSpringAnimation.start();',a)
  bodies+=['void installNativeSpringCallback(){final long springGeneration=instantNavigation==null?0:instantNavigation.generation();'+source[a:b]+'}']
  if 'private boolean isObsoleteInstantFrame(' in source:bodies+=[method(source,'private boolean isObsoleteInstantFrame(')]
 if 'private boolean prepareInstantBack(' in source:bodies+=[method(source,'private boolean prepareInstantBack('),method(source,'private boolean hasInstantBackModal(')]
 if 'private void clearInstantBackSeed(' in source:bodies+=[method(source,'private void clearInstantBackSeed(')]
 if 'private boolean finishClosingPreview()' in source:bodies+=[method(source,'private boolean finishClosingPreview()')]
 a=source.index('public void closeLastFragment(boolean animated, boolean forceNoAnimation)');b=source.index('        if (parentActivity.getCurrentFocus()',a)
 bodies+=[source[a:b]+' beginClose(getLastFragment()); }']
 return '''import java.util.*;import org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator;public class PreviewRegression {
 FlexyInstantNavigationCoordinator instantNavigation;boolean instantSwipeSettlingClosing;boolean instantBackSeed;float instantBackValue,instantBackVelocity;long instantBackGeneration,instantBackDialog;static final float SPRING_MULTIPLIER=1000;boolean USE_SPRING_ANIMATION=true;
 static class ChatActivity extends BaseFragment {long getDialogId(){return 42;}}
 static class Dialog{boolean showing;Dialog(boolean value){showing=value;}boolean isShowing(){return showing;}}
 static class LaunchActivity{static LaunchActivity instance;Dialog getVisibleDialog(){return null;}}
 static class View{static final int VISIBLE=0;}
 static class BaseFragment {Dialog dialog;boolean sheet,allowBack=true;Dialog getVisibleDialog(){return dialog;}boolean hasSheet(){return sheet;}boolean closeLastFragment(){return false;}boolean onBackPressed(boolean p){return allowBack;}}
 static class Container {boolean isKeyboardVisible;float x;boolean isAttachedToWindow(){return true;}int getVisibility(){return 0;}int getChildCount(){return 1;}void setAlpha(float f){}void setScaleX(float f){}void setScaleY(float f){}void setTranslationX(float f){x=f;}void setTranslationY(float f){}}
 static class Animator{boolean cancelled;Runnable callback;void removeAllListeners(){callback=null;}void cancel(){if(cancelled)return;cancelled=true;if(callback!=null)callback.run();}} static class AnimatorSet extends Animator{} static class SpringAnimation{interface End{void onEnd(SpringAnimation a,boolean c,float v,float speed);}boolean cancelled;boolean canContinue(){return false;}float continuationValue(){return 0;}float continuationVelocity(){return 0;}boolean isRunning(){return !cancelled;}End listener;void addEndListener(End l){listener=l;}void finish(){listener.onEnd(this,false,1,0);}void cancel(){if(cancelled)return;cancelled=true;if(listener!=null)listener.onEnd(this,true,0,0);}}
 static class AndroidUtilities{static void cancelRunOnUIThread(Runnable r){}}
 static class GroupCallPip{static boolean onBackPressed(){return false;}}
 static class Bar {boolean isActionModeShowed(){return false;}boolean isSearchFieldVisible;void closeSearchField(){}}
 interface Delegate{boolean needCloseLastFragment(PreviewRegression p);}
 ArrayList<BaseFragment> fragmentsStack=new ArrayList<>();BaseFragment sheetFragment,newFragment,oldFragment;Bar currentActionBar;Delegate delegate;
 boolean predictiveBackInProgress,inActionMode,isSheet,isLayersLayout,isRightLayout;float swipeProgress;
 boolean inPreviewMode,transitionAnimationPreviewMode,transitionAnimationInProgress,animationInProgress,startedTracking,previewOpenAnimationInProgress;
 long transitionAnimationStartTime;Object layoutToIgnore,springRouteBackgroundDrawable,previewMenu;float springRouteYRatio;boolean USE_ACTIONBAR_CROSSFADE;
 Container containerView=new Container(),containerViewBack=new Container();Animator currentAnimation;SpringAnimation currentSpringAnimation;
 Runnable onCloseAnimationEndRunnable,onOpenAnimationEndRunnable,waitingForKeyboardCloseRunnable,animationRunnable,delayedOpenAnimationRunnable;
 float inner;void setInnerTranslationX(float value){inner=value;}
 void setAlpha(float f){}void invalidateActionBars(){}void checkNeedRebuild(){}boolean storyViewerAttached(){return false;}
 BaseFragment getLastFragment(){return fragmentsStack.isEmpty()?null:fragmentsStack.get(fragmentsStack.size()-1);}
 void closeLastFragment(boolean animated){closeLastFragment(animated,false);}
 int closeRequests;void beginClose(BaseFragment target){closeRequests++;transitionAnimationStartTime=System.currentTimeMillis();transitionAnimationInProgress=true;layoutToIgnore=containerView;
 onCloseAnimationEndRunnable=()->{fragmentsStack.remove(target);inPreviewMode=false;previewMenu=null;};}
 void drain(){onAnimationEndCheck(true);}
 void preview(){fragmentsStack.add(new BaseFragment());inPreviewMode=true;previewMenu=new Object();}
_METHODS_
 static void check(boolean v){if(!v)throw new AssertionError("preview close consumed underlying navigation");}
 static PreviewRegression create(){PreviewRegression p=new PreviewRegression();p.fragmentsStack.add(new BaseFragment());return p;}
 public static void main(String[]args){boolean original=args.length>0;
 PreviewRegression release=create();release.preview();release.finishPreviewFragment();release.finishPreviewFragment();release.drain();
 if(original){check(release.fragmentsStack.isEmpty());return;}
 check(release.fragmentsStack.size()==1);check(!release.inPreviewMode&&!release.transitionAnimationInProgress&&release.layoutToIgnore==null&&release.previewMenu==null);
 PreviewRegression back=create();back.preview();back.finishPreviewFragment();back.onBackPressed();back.drain();check(back.fragmentsStack.size()==1);
 PreviewRegression early=create();early.fragmentsStack.add(new BaseFragment());early.transitionAnimationInProgress=true;early.transitionAnimationPreviewMode=true;early.transitionAnimationStartTime=System.currentTimeMillis();early.onOpenAnimationEndRunnable=()->{early.inPreviewMode=true;early.previewMenu=new Object();};early.onBackPressed();early.drain();check(early.fragmentsStack.size()==1&&!early.inPreviewMode);
 for(int n=0;n<200;n++){release.preview();release.finishPreviewFragment();release.onBackPressed();release.finishPreviewFragment();release.drain();check(release.fragmentsStack.size()==1);}
 release.fragmentsStack.add(new BaseFragment());release.onBackPressed();release.drain();check(release.fragmentsStack.size()==1);
 }}'''.replace('_METHODS_','\n'.join(bodies)).replace('Animator currentAnimation;', 'Animator currentAnimation;' if 'private Animator currentAnimation;' in source else 'AnimatorSet currentAnimation;')
class PreviewNavigation(unittest.TestCase):
 def test_actual_native_double_close_reproduces_before_and_preserves_home_after(self):
  fixed=(ROOT/PATH).read_text();old=subprocess.check_output(['git','show',BASE+':'+PATH],cwd=ROOT,text=True)
  for source,args in [(old,['original']),(fixed,[])]:
   with tempfile.TemporaryDirectory() as d:
    file=Path(d)/'PreviewRegression.java';file.write_text(fixture(source));subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(file),str(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyInstantNavigationCoordinator.java')],check=True);subprocess.run(['java','-cp',d,'PreviewRegression',*args],check=True)
 def test_recorded_delta_preserves_the_rest_of_native_navigation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/PATH;p.parent.mkdir(parents=True);p.write_bytes(restore1271(PATH,(ROOT/PATH).read_bytes()))
   subprocess.run(['git','apply','--reverse','-'],cwd=d,input=(ROOT/'tools/connected_alpha/preview_navigation.patch').read_bytes(),check=True,capture_output=True)
   self.assertEqual(p.read_bytes(),subprocess.check_output(['git','show',BASE+':'+PATH],cwd=ROOT))

class InstantCompletionOwnership(unittest.TestCase):
 def run_fixture(self,source,should_pass):
  code=fixture(source)
  extras="""
  static int installed;
  static void newer(PreviewRegression p){
   installed++;
   p.instantNavigation.begin(FlexyInstantNavigationCoordinator.State.OPENING,
    new FlexyInstantNavigationCoordinator.Intent(FlexyInstantNavigationCoordinator.Kind.OPEN_CHAT,123,null),false);
   p.transitionAnimationInProgress=true;
   p.currentAnimation=new AnimatorSet();p.currentSpringAnimation=new SpringAnimation();
   p.animationRunnable=()->{};p.containerView.x=123;p.inner=123;
  }
  static PreviewRegression ownership(boolean opening,boolean nestedCancel){
   PreviewRegression p=create();p.instantNavigation=new FlexyInstantNavigationCoordinator();
   p.instantNavigation.begin(opening?FlexyInstantNavigationCoordinator.State.OPENING:FlexyInstantNavigationCoordinator.State.CLOSING,
    new FlexyInstantNavigationCoordinator.Intent(FlexyInstantNavigationCoordinator.Kind.BACK,42,null),true);
   p.transitionAnimationInProgress=true;
   if(opening)p.onOpenAnimationEndRunnable=()->newer(p);else p.onCloseAnimationEndRunnable=()->newer(p);
   p.currentSpringAnimation=new SpringAnimation();
   if(opening||nestedCancel){p.currentAnimation=new AnimatorSet();if(nestedCancel)p.currentAnimation.callback=()->p.onAnimationEndCheck(true);}
   return p;
  }
  static void verifyOwnership(){
   for(int mode=0;mode<3;mode++){
    PreviewRegression p=ownership(mode==1,mode==2);SpringAnimation oldSpring=p.currentSpringAnimation;Animator oldAnimator=p.currentAnimation;
    int before=installed;p.onAnimationEndCheck(true);
    check(installed==before+1);check(p.transitionAnimationInProgress);
    check(p.currentSpringAnimation!=oldSpring&&!p.currentSpringAnimation.cancelled);
    check(p.currentAnimation!=oldAnimator&&!p.currentAnimation.cancelled);
    check(oldSpring.cancelled);check(p.containerView.x==123);
    check(p.instantNavigation.state()==FlexyInstantNavigationCoordinator.State.OPENING);
   }
   PreviewRegression spring=ownership(false,false);spring.installNativeSpringCallback();spring.currentSpringAnimation.finish();
   check(spring.inner==123);check(spring.currentAnimation!=null&&!spring.currentAnimation.cancelled);
  }
  """
  code=code.replace(' public static void main(String[]args)',extras+' public static void main(String[]args)').replace('boolean original=args.length>0;','boolean original=args.length>0;verifyOwnership();')
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'PreviewRegression.java';path.write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(path),str(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyInstantNavigationCoordinator.java')],check=True)
   result=subprocess.run(['java','-cp',d,'PreviewRegression'],capture_output=True)
   self.assertEqual(should_pass,result.returncode==0,result.stderr.decode())
 def test_native_completion_preserves_new_owner_and_stops_old_controllers(self):
  source=(ROOT/PATH).read_text();self.run_fixture(source,True)
  guard=method(source,'private boolean isObsoleteInstantCompletion(')
  mutant=source.replace(guard,guard[:guard.index('{')]+'{return false;}')
  self.run_fixture(mutant,False)
  tail="                if (instantNavigation == null || instantNavigation.isCurrent(endingGeneration)) setInnerTranslationX(0);"
  self.assertIn(tail,source)
  self.run_fixture(source.replace(tail,"                setInnerTranslationX(0);"),False)

class OpeningBackOwnership(unittest.TestCase):
 def test_same_native_back_closes_ready_opening_and_keeps_newer_destinations(self):
  code=fixture((ROOT/PATH).read_text())
  extras="""
  static PreviewRegression opening(){PreviewRegression p=create();p.fragmentsStack.add(new ChatActivity());p.transitionAnimationInProgress=true;p.transitionAnimationStartTime=System.currentTimeMillis();p.onOpenAnimationEndRunnable=()->{};p.currentSpringAnimation=new SpringAnimation();return p;}
  static void verifyOpeningBack(){
   PreviewRegression p=opening();SpringAnimation old=p.currentSpringAnimation;p.onBackPressed();
   check(p.closeRequests==1&&old.cancelled&&p.onOpenAnimationEndRunnable==null&&p.onCloseAnimationEndRunnable!=null);
   p.onBackPressed();check(p.closeRequests==1);p.drain();check(p.fragmentsStack.size()==1);
   PreviewRegression newer=opening();newer.onOpenAnimationEndRunnable=()->{newer.instantNavigation.begin(FlexyInstantNavigationCoordinator.State.OPENING,new FlexyInstantNavigationCoordinator.Intent(FlexyInstantNavigationCoordinator.Kind.OPEN_CHAT,99,null),false);newer.transitionAnimationInProgress=true;newer.currentSpringAnimation=new SpringAnimation();newer.containerView.x=99;};newer.onBackPressed();
   check(newer.closeRequests==0&&newer.containerView.x==99&&newer.instantNavigation.intent().destinationId==99);
   PreviewRegression modal=opening();modal.getLastFragment().dialog=new Dialog(true);modal.onBackPressed();check(modal.closeRequests==0&&!modal.currentSpringAnimation.cancelled);
   PreviewRegression lateModal=opening();lateModal.onOpenAnimationEndRunnable=()->lateModal.getLastFragment().dialog=new Dialog(true);lateModal.onBackPressed();check(lateModal.closeRequests==0&&lateModal.fragmentsStack.size()==2);
   PreviewRegression veto=opening();veto.getLastFragment().allowBack=false;veto.onBackPressed();check(veto.closeRequests==0&&veto.fragmentsStack.size()==2&&veto.onOpenAnimationEndRunnable==null);
  }
  """
  code=code.replace(' public static void main(String[]args)',extras+' public static void main(String[]args)').replace('boolean original=args.length>0;','boolean original=args.length>0;verifyOpeningBack();')
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'PreviewRegression.java';path.write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(path),str(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyInstantNavigationCoordinator.java')],check=True)
   subprocess.run(['java','-cp',d,'PreviewRegression'],check=True)
