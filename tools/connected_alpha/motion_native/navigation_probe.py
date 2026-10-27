"""Actual navigation renderer/callback excerpts with real Android containers; fragments are explicit doubles."""
from player_probe import method

def write(put,root,source):
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 timed=method(s,'    private void startFlexyTimedLayoutAnimation(')
 cleanup=method(method(s,'    private void onAnimationEndCheck('),'        if (currentSpringAnimation != null)')
 start=s.index('    private void startLayoutAnimation(')
 a=s.index('            currentSpringAnimation.addUpdateListener(',start)
 b=s.index('            currentSpringAnimation.start();',a)
 spring=s[a:b]
 put('NavigationMotionProbe.java','''import android.view.*;import android.widget.*;import android.graphics.drawable.*;import androidx.core.graphics.ColorUtils;import androidx.core.math.MathUtils;
import androidx.dynamicanimation.animation.FloatValueHolder;import androidx.dynamicanimation.animation.SpringForce;import app.flexygram.motion.SpringAnimation;import org.telegram.ui.Components.CubicBezierInterpolator;import org.telegram.ui.ActionBar.Theme;import org.telegram.messenger.AndroidUtilities;
public class NavigationMotionProbe extends FrameLayout {
 final FrameLayout containerView,containerViewBack;final View previewMenu;final ColorDrawable previewBackgroundDrawable=new ColorDrawable();
 static final float SPRING_MULTIPLIER=1000;float animationProgress,swipeProgress,inner;boolean USE_ACTIONBAR_CROSSFADE=true;long transitionAnimationStartTime;Object springRouteBackgroundDrawable;
 final android.view.animation.OvershootInterpolator overshootInterpolator=new android.view.animation.OvershootInterpolator();final android.view.animation.DecelerateInterpolator decelerateInterpolator=new android.view.animation.DecelerateInterpolator();
 SpringAnimation currentSpringAnimation;public int completions;public boolean lastCancelled;
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
'''+timed+'}')
 p=source/'NavigationMotionProbe.java';p.write_text(p.read_text().replace('__CLEANUP__',cleanup))
 p=source/'org/telegram/ui/ActionBar/Theme.java';p.write_text(p.read_text().replace('public class Theme {','public class Theme {public static final android.graphics.drawable.ColorDrawable moveUpDrawable=new android.graphics.drawable.ColorDrawable();'))

 p=source/"org/telegram/messenger/AndroidUtilities.java";p.write_text(p.read_text().replace("public class AndroidUtilities {","public class AndroidUtilities {public static float lerp(float a,float b,float t){return a+(b-a)*t;}"))
