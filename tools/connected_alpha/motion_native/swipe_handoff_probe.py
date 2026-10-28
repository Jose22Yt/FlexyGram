"""Exact settling renderer, handoff and full slide-completion body; fragment/services remain explicit doubles.

Real Android containers, Button, dispatch, spring and coordinator. The initial
edge swipe is staged, not injected or claimed to be a full physical gesture.
"""
from player_probe import method
from gesture_support import fields

def write(put, root):
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 a=s.index('        if (USE_SPRING_ANIMATION) {',s.index('    private void animateBackEndAnimation('))
 spring=method(s[a:],'        if (USE_SPRING_ANIMATION)')
 body='\n'.join(method(s,x) for x in [
  '    private void clearInstantGesture(',
  '    private boolean isObsoleteInstantFrame(',
  '    private void renderInstantGestureValue(',
  '    private boolean tryHandoffSettlingChatDown(',
  '    private boolean hasInstantBackModal(',
  '    private void onSlideAnimationEnd(',
  '    private void resetPredictiveBackState(',
  '    public boolean onInterceptTouchEvent('])
 put('SwipeHandoffProbe.java','''import android.view.*;import android.widget.*;import android.animation.Animator;import java.util.ArrayList;import androidx.dynamicanimation.animation.*;import androidx.core.math.MathUtils;import app.flexygram.motion.SpringAnimation;import org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator;import org.telegram.ui.ActionBar.FlexyNavigationHandoffPolicy;
public class SwipeHandoffProbe extends FrameLayout {
 static final float SPRING_MULTIPLIER=1000,SPRING_STIFFNESS=900;
 static class LayoutContainer extends FrameLayout {LayoutContainer(android.content.Context c){super(c);}}
 static class Bar extends View {Bar(android.content.Context c){super(c);}boolean shouldAddToContainer(){return true;}}
 static class Dialog {boolean showing=true;boolean isShowing(){return showing;}}
 static class LaunchActivity {static LaunchActivity instance;Dialog getVisibleDialog(){return null;}}
 static class BaseFragment {View fragmentView;Bar actionBar;Dialog dialog;boolean sheet;int destroys,pauses,resumes;void prepareFragmentToSlide(boolean a,boolean b){}void onPause(){pauses++;}void onFragmentDestroy(){destroys++;}void setParentLayout(Object p){}void onResume(){resumes++;}void onBecomeFullyVisible(){}void onRemoveFromParent(){}void detachSheets(){}void onTransitionAnimationProgress(boolean a,float p){}Dialog getVisibleDialog(){return dialog;}boolean hasSheet(){return sheet;}}
 static class ChatActivity extends BaseFragment{}static class MainTabsActivity extends BaseFragment{}static class DialogsActivity extends BaseFragment{}
 static class AndroidUtilities {static float lerp(float a,float b,float t){return a+(b-a)*t;}}
 final ArrayList<BaseFragment> fragmentsStack=new ArrayList<>();final ChatActivity outgoing=new ChatActivity();final BaseFragment destination=new MainTabsActivity();
 LayoutContainer containerView,containerViewBack;View sheetContainer;Bar currentActionBar;Object layoutToIgnore,springRouteBackgroundDrawable,predictiveBackBackgroundDrawable;
 BaseFragment sheetFragment;SpringAnimation currentSpringAnimation;Animator backAnimator;VelocityTracker velocityTracker;FlexyInstantNavigationCoordinator instantNavigation;
 final app.exteraless.utils.PredictiveBackAnimationHelper predictiveBackAnimation=new app.exteraless.utils.PredictiveBackAnimationHelper();
 boolean instantSwipeSettlingClosing,animationInProgress,startedTracking,transitionAnimationInProgress,predictiveBackInProgress,predictiveBackHasProgress,m3PredictiveBack,inPreviewMode,transitionAnimationPreviewMode,previewOpenAnimationInProgress,inActionMode,isSheet,isLayersLayout,isRightLayout;
 boolean USE_SPRING_ANIMATION=true,USE_ACTIONBAR_CROSSFADE=true;float springRouteYRatio,inner,swipeProgress;int commits,clicks,downs,ups;long downTime,upTime;
 final Button row;
 public SwipeHandoffProbe(android.content.Context c){super(c);containerView=new LayoutContainer(c);containerViewBack=new LayoutContainer(c);row=new Button(c){public boolean onTouchEvent(MotionEvent e){if(e.getActionMasked()==MotionEvent.ACTION_DOWN){downs++;downTime=e.getEventTime();}if(e.getActionMasked()==MotionEvent.ACTION_UP){ups++;upTime=e.getEventTime();}return super.onTouchEvent(e);}};row.setText("Synthetic chat B");row.setOnClickListener(v->clicks++);containerViewBack.addView(row,new FrameLayout.LayoutParams(300,96));row.setY(200);destination.fragmentView=row;View chat=new View(c);containerView.addView(chat,new FrameLayout.LayoutParams(300,600));outgoing.fragmentView=chat;addView(containerViewBack,new FrameLayout.LayoutParams(300,600));addView(containerView,new FrameLayout.LayoutParams(300,600));fragmentsStack.add(destination);fragmentsStack.add(outgoing);}
 BaseFragment getLastFragment(){return fragmentsStack.isEmpty()?null:fragmentsStack.get(fragmentsStack.size()-1);}BaseFragment getBackgroundFragment(){return fragmentsStack.get(fragmentsStack.size()-2);}
 static int dp(float v){return (int)v;}void setInnerTranslationX(float v){inner=v;}void invalidateActionBars(){}void checkBlackScreen(String tag){}void onFragmentStackChanged(String tag){commits++;}boolean storyViewerAttached(){return false;}boolean checkTransitionAnimation(){return false;}boolean tryHandoffClosingChatDown(MotionEvent e){return false;}
 public void stageReleasedSwipe(float initialProgress,boolean revert,float velX){startedTracking=true;float x=initialProgress*getWidth();containerView.setTranslationX(x);containerViewBack.setTranslationX(-(1-initialProgress)*.35f*getWidth());containerView.setScaleX(1-.15f*initialProgress);containerView.setScaleY(1-.15f*initialProgress);boolean backAnimation=revert;
'''+spring+'''
 }
 public void stop(){if(currentSpringAnimation!=null)currentSpringAnimation.cancel();}
'''+fields(s)+'\n'+body+'}')
