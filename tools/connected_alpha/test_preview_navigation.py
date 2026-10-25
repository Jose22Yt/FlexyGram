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
 if 'private boolean finishClosingPreview()' in source:bodies+=[method(source,'private boolean finishClosingPreview()')]
 a=source.index('public void closeLastFragment(boolean animated, boolean forceNoAnimation)');b=source.index('        if (parentActivity.getCurrentFocus()',a)
 bodies+=[source[a:b]+' beginClose(getLastFragment()); }']
 return '''import java.util.*;public class PreviewRegression {
 static class BaseFragment {boolean closeLastFragment(){return false;}boolean onBackPressed(boolean p){return true;}}
 static class Container {void setAlpha(float f){}void setScaleX(float f){}void setScaleY(float f){}void setTranslationX(float f){}void setTranslationY(float f){}}
 static class AnimatorSet{void cancel(){}} static class SpringAnimation{void cancel(){}}
 static class AndroidUtilities{static void cancelRunOnUIThread(Runnable r){}}
 static class GroupCallPip{static boolean onBackPressed(){return false;}}
 static class Bar {boolean isActionModeShowed(){return false;}boolean isSearchFieldVisible;void closeSearchField(){}}
 interface Delegate{boolean needCloseLastFragment(PreviewRegression p);}
 ArrayList<BaseFragment> fragmentsStack=new ArrayList<>();BaseFragment sheetFragment,newFragment,oldFragment;Bar currentActionBar;Delegate delegate;
 boolean inPreviewMode,transitionAnimationPreviewMode,transitionAnimationInProgress,animationInProgress,startedTracking,previewOpenAnimationInProgress;
 long transitionAnimationStartTime;Object layoutToIgnore,springRouteBackgroundDrawable,previewMenu;float springRouteYRatio;boolean USE_ACTIONBAR_CROSSFADE;
 Container containerView=new Container(),containerViewBack=new Container();AnimatorSet currentAnimation;SpringAnimation currentSpringAnimation;
 Runnable onCloseAnimationEndRunnable,onOpenAnimationEndRunnable,waitingForKeyboardCloseRunnable,animationRunnable,delayedOpenAnimationRunnable;
 void setAlpha(float f){}void invalidateActionBars(){}void checkNeedRebuild(){}boolean storyViewerAttached(){return false;}
 BaseFragment getLastFragment(){return fragmentsStack.isEmpty()?null:fragmentsStack.get(fragmentsStack.size()-1);}
 void closeLastFragment(boolean animated){closeLastFragment(animated,false);}
 void beginClose(BaseFragment target){transitionAnimationStartTime=System.currentTimeMillis();transitionAnimationInProgress=true;layoutToIgnore=containerView;
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
 }}'''.replace('_METHODS_','\n'.join(bodies))
class PreviewNavigation(unittest.TestCase):
 def test_actual_native_double_close_reproduces_before_and_preserves_home_after(self):
  fixed=(ROOT/PATH).read_text();old=subprocess.check_output(['git','show',BASE+':'+PATH],cwd=ROOT,text=True)
  for source,args in [(old,['original']),(fixed,[])]:
   with tempfile.TemporaryDirectory() as d:
    file=Path(d)/'PreviewRegression.java';file.write_text(fixture(source));subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(file)],check=True);subprocess.run(['java','-cp',d,'PreviewRegression',*args],check=True)
 def test_recorded_delta_preserves_the_rest_of_native_navigation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/PATH;p.parent.mkdir(parents=True);p.write_bytes(restore1271(PATH,(ROOT/PATH).read_bytes()))
   subprocess.run(['git','apply','--reverse','-'],cwd=d,input=(ROOT/'tools/connected_alpha/preview_navigation.patch').read_bytes(),check=True,capture_output=True)
   self.assertEqual(p.read_bytes(),subprocess.check_output(['git','show',BASE+':'+PATH],cwd=ROOT))
