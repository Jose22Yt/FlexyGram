from pathlib import Path

def method(text,anchor):
 start=text.index(anchor);end=text.index('{',start)+1;level=1;i=end
 while level:
  level+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[start:i]

def write(dest,root):
 source=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 methods='\n'.join(method(source,anchor) for anchor in [
  'private void nativeInstantTouchDown(', 'private void finishNavigationForInput(',
  'private void onAnimationEndCheck(', 'private void onCloseAnimationEnd()', 'private void onOpenAnimationEnd()'])
 host='''import android.content.Context;import android.view.*;import android.widget.*;import android.animation.*;
 public class NavigationProbe extends FrameLayout{
  static class BaseFragment{Object sheet;Object getLastSheet(){return sheet;}}
  static class SpringAnimation{int cancelled;Runnable callback;void cancel(){cancelled++;if(callback!=null)callback.run();}}
  static class AndroidUtilities{static void cancelRunOnUIThread(Runnable r){}}
  boolean storyModal;boolean storyViewerAttached(){return storyModal;}
  BaseFragment fragment=new BaseFragment();FrameLayout containerView,containerViewBack;
  boolean completingTransition,transitionAnimationInProgress,transitionAnimationPreviewMode,inPreviewMode,previewOpenAnimationInProgress,inActionMode,predictiveInput,startedTracking,animationInProgress,settlingBackAnimation;
  Object previewMenu,sheetFragment,layoutToIgnore,newFragment,oldFragment,springRouteBackgroundDrawable;
  float springRouteYRatio,innerTranslationX;long transitionAnimationStartTime;
  AnimatorSet currentAnimation,backAnimator;SpringAnimation currentSpringAnimation;
  Runnable animationRunnable,waitingForKeyboardCloseRunnable,delayedOpenAnimationRunnable,onCloseAnimationEndRunnable,onOpenAnimationEndRunnable;
  static final boolean USE_ACTIONBAR_CROSSFADE=false;int finishes,slides;
  NavigationProbe(Context c){super(c);containerView=new FrameLayout(c);containerViewBack=new FrameLayout(c);addView(containerView,new LayoutParams(-1,-1));}
  BaseFragment getLastFragment(){return fragment;}void checkNeedRebuild(){}void invalidateActionBars(){}
  void setInnerTranslationX(float x){innerTranslationX=x;}boolean finishClosingPreview(){return false;}
  void resetPredictiveBackState(){predictiveInput=false;}
  void onSlideAnimationEnd(boolean back){animationInProgress=false;startedTracking=false;slides++;}
  public boolean dispatchTouchEvent(MotionEvent event){nativeInstantTouchDown(event);return super.dispatchTouchEvent(event);}
  void begin(View target,boolean close){transitionAnimationInProgress=true;Runnable done=()->{finishes++;containerView.removeAllViews();containerView.addView(target,new LayoutParams(-1,-1));};if(close)onCloseAnimationEndRunnable=done;else onOpenAnimationEndRunnable=done;}
  void finishNow(){onAnimationEndCheck(true);}
  METHODS
 }
 '''.replace('METHODS',methods)
 (dest/'NavigationProbe.java').write_text(host)
 for rel in ['app/flexygram/animation/FastMotionTiming.java','app/exteraless/player/Spring.java','app/flexygram/bubbles/interaction/BubbleTapMotion.java','app/flexygram/bubbles/interaction/DampedSpringCurve.java']:
  target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text((root/'TMessagesProj/src/main/java'/rel).read_text())
