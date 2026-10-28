"""Actual navigation renderer/callback excerpts with real Android containers; fragments are explicit doubles."""
from player_probe import method

def write(put,root,source):
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 timed=method(s,'    private void startFlexyTimedLayoutAnimation(')
 alpha=method(s,'    private Animator createRootAlphaTransition(')
 predictive=method(s,'    private Animator createPredictiveBackEndTransition(')
 gesture=method(s,'    private void applyPredictiveBackProgress(')
 settle=method(s,'    private void animatePredictiveBackEndAnimation(')
 reset=method(s,'    private void resetPredictiveBackState(')
 cleanup=method(method(s,'    private void onAnimationEndCheck('),'        if (currentSpringAnimation != null)')
 start=s.index('    private void startLayoutAnimation(')
 a=s.index('            currentSpringAnimation.addUpdateListener(',start)
 b=s.index('            currentSpringAnimation.start();',a)
 spring=s[a:b]
 put('NavigationMotionProbe.java','''import android.animation.*;import java.util.ArrayList;import android.view.*;import android.widget.*;import android.graphics.drawable.*;import androidx.core.graphics.ColorUtils;import androidx.core.math.MathUtils;
import androidx.dynamicanimation.animation.FloatValueHolder;import androidx.dynamicanimation.animation.SpringForce;import app.flexygram.motion.SpringAnimation;import org.telegram.ui.Components.CubicBezierInterpolator;import org.telegram.ui.ActionBar.Theme;import org.telegram.messenger.AndroidUtilities;
public class NavigationMotionProbe extends FrameLayout {
 public final View backgroundView=new View(getContext());public android.animation.Animator alpha(boolean opening){return createRootAlphaTransition(opening);}
 public boolean predictiveBackHasProgress,animationInProgress,predictiveBackInProgress,m3PredictiveBack,backAnimatorIsBack;public float predictiveBackY;public Object predictiveBackBackgroundDrawable,layoutToIgnore;public Animator backAnimator;public int slideCompletions;public boolean slideCancelled;
 public final app.exteraless.utils.PredictiveBackAnimationHelper predictiveBackAnimation=new app.exteraless.utils.PredictiveBackAnimationHelper();
 public void predictive(boolean revert){animatePredictiveBackEndAnimation(revert);}public Animator predictiveTimeline(boolean revert){return createPredictiveBackEndTransition(revert,predictiveBackAnimation.getProgress(),containerView.getAlpha(),predictiveBackAnimation.getSlideDistance());}void onSlideAnimationEnd(boolean reverted){slideCompletions++;slideCancelled=reverted;animationInProgress=false;layoutToIgnore=null;}static float clamp01(float v){return Math.max(0,Math.min(1,v));}
 final FrameLayout containerView,containerViewBack;final View previewMenu;final ColorDrawable previewBackgroundDrawable=new ColorDrawable();
 static final float SPRING_MULTIPLIER=1000;float animationProgress,swipeProgress,inner;boolean USE_ACTIONBAR_CROSSFADE=true;long transitionAnimationStartTime;Object springRouteBackgroundDrawable;
 final android.view.animation.OvershootInterpolator overshootInterpolator=new android.view.animation.OvershootInterpolator();final android.view.animation.DecelerateInterpolator decelerateInterpolator=new android.view.animation.DecelerateInterpolator();
 org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator instantNavigation;SpringAnimation currentSpringAnimation;public int completions;public boolean lastCancelled;
 static class BaseFragment {interface AttachedSheet{boolean attachedToParent();int getNavigationBarColor(int color);}}
 static class Fragment {public java.util.ArrayList<BaseFragment.AttachedSheet> sheetsStack;int updates,color=0xff333333;float progress;void onTransitionAnimationProgress(boolean opening,float v){updates++;progress=v;}Integer getNavigationBarColor(){return color;}void setNavigationBarColor(int v){color=v;}boolean isSupportEdgeToEdge(){return false;}}
 Fragment newFragment=new Fragment(),oldFragment=new Fragment(),sheetFragment;
 public NavigationMotionProbe(android.content.Context c){super(c);containerView=new FrameLayout(c);containerViewBack=new FrameLayout(c);previewMenu=new View(c);addView(containerViewBack,new FrameLayout.LayoutParams(300,600));addView(containerView,new FrameLayout.LayoutParams(300,600));addView(previewMenu,new FrameLayout.LayoutParams(100,100));}
 static int dp(float v){return (int)v;}void setInnerTranslationX(float v){inner=v;}
 void onAnimationEndCheck(boolean cancelled){__CLEANUP__completions++;lastCancelled=cancelled;containerView.setScaleX(1);containerView.setScaleY(1);containerViewBack.setScaleX(1);containerViewBack.setScaleY(1);containerView.setAlpha(1);containerViewBack.setAlpha(1);containerView.setTranslationX(0);containerViewBack.setTranslationX(0);}
 public void timed(boolean open,boolean preview){startFlexyTimedLayoutAnimation(open,preview);}
 public void spring(boolean open,boolean preview){currentSpringAnimation=new SpringAnimation(this,new FloatValueHolder(0)).setSpring(new SpringForce(SPRING_MULTIPLIER));
'''+spring+'''currentSpringAnimation.start();}
 public void abort(){if(currentSpringAnimation!=null){SpringAnimation old=currentSpringAnimation;currentSpringAnimation=null;old.cancel();}}
'''+alpha+'\n'+predictive+'\n'+gesture+'\n'+settle+'\n'+reset+'\n'+timed+'}')
 p=source/'NavigationMotionProbe.java';p.write_text(p.read_text().replace('__CLEANUP__',cleanup))
 p=source/'org/telegram/ui/ActionBar/Theme.java';p.write_text(p.read_text().replace('public class Theme {','public class Theme {public static final android.graphics.drawable.ColorDrawable moveUpDrawable=new android.graphics.drawable.ColorDrawable();'))

 p=source/"org/telegram/messenger/AndroidUtilities.java";p.write_text(p.read_text().replace("public class AndroidUtilities {","public class AndroidUtilities {public static float lerp(float a,float b,float t){return a+(b-a)*t;}"))

 # Real geometry is compiled, while account/navigation containers remain explicit doubles.
 put('app/exteraless/utils/PredictiveBackAnimationHelper.java',(root/'TMessagesProj/src/main/java/app/exteraless/utils/PredictiveBackAnimationHelper.java').read_text())
 put('org/telegram/messenger/Utilities.java','package org.telegram.messenger;public class Utilities {public static float clamp(float v,float max,float min){return Math.max(min,Math.min(max,v));}public static float clamp01(float v){return clamp(v,1,0);}}')
 put('org/telegram/ui/ActionBar/BaseFragment.java','package org.telegram.ui.ActionBar;public class BaseFragment {public android.view.View fragmentView;public Theme.ResourcesProvider getResourceProvider(){return null;}}')
 put('org/telegram/ui/ProfileActivity.java','package org.telegram.ui;public class ProfileActivity extends org.telegram.ui.ActionBar.BaseFragment {}')
 put('org/telegram/ui/ViewPagerActivity.java','package org.telegram.ui;public class ViewPagerActivity extends org.telegram.ui.ActionBar.BaseFragment {public org.telegram.ui.ActionBar.BaseFragment getCurrentVisibleFragment(){return null;}}')
 p=source/'org/telegram/ui/ActionBar/Theme.java';p.write_text(p.read_text().replace('public class Theme {','public class Theme {public static int key_windowBackgroundGray=4;'))
