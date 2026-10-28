"""Exact native predictive admission/progress and spring settlement from a real opening actor.

Containers, bridge, clock, coordinator and renderer are real. Fragment/services,
prepareForMoving and slide stack transactions are explicit doubles. This is not
a full application or a physical Android17/OS dispatcher test.
"""
from player_probe import method
import re

def write(put,root):
 from opening_back_probe import write as write_opening
 captured={}
 write_opening(lambda name,code:captured.update({name:code}),root)
 code=captured['OpeningBackProbe.java'].replace('OpeningBackProbe','GestureOpeningProbe')
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 code=code.replace(method(code,' static class Animator{'),'').replace(method(code,' static class AnimatorSet '),'')
 code=code.replace('import java.util.*;','import java.util.*;import static org.telegram.messenger.Utilities.clamp01;import android.animation.Animator;import android.animation.ObjectAnimator;import android.animation.AnimatorListenerAdapter;import android.animation.ValueAnimator;import android.animation.AnimatorSet;import android.view.VelocityTracker;import org.telegram.ui.Components.CubicBezierInterpolator;')
 code=code.replace('static class BaseFragment {','static class BaseFragment {boolean slideAllowed=true;int slideBegins;Runnable afterBegin;boolean hasShownSheet(){return sheet;}boolean canBeginSlide(){return slideAllowed;}void onBeginSlide(){slideBegins++;if(afterBegin!=null)afterBegin.run();}')
 code=code.replace('static class AndroidUtilities{','static class AndroidUtilities{static final android.graphics.Point displaySize=new android.graphics.Point(300,600);static void hideKeyboard(android.view.View v){}')
 code=code.replace('public GestureOpeningProbe(android.content.Context c){super(c);','public GestureOpeningProbe(android.content.Context c){super(c);parentActivity=(android.app.Activity)c;NaConfig.style=BACK_ANIMATION_SPRING;')
 anchors=[
 '    private boolean isObsoleteInstantAnimator(',
 '    private boolean m3BackTransition(', '    private boolean newBackTransitions(',
 '    private Animator createPredictiveBackEndTransition(', '    private void animatePredictiveBackEndAnimation(',
 '    private boolean consumeAbandonedInstantGesture(',
 '    private boolean prepareInstantGestureBack(', '    private void adoptInstantGesture(',
 '    private void renderInstantGestureValue(', '    private boolean applyInstantGestureProgress(',
 '    private float prepareInstantGestureSettleVelocity(', '    private void resetPredictiveBackState(',
 '    public boolean onBackStarted(', '    public void onBackProgress(float t)',
 '    public void onBackProgress(float t, float touchY)', '    public void onBackCancelled(',
 '    public void onBackInvoked(', '    public boolean isInPreviewMode()',
 '    private void applyPredictiveBackProgress('
 ]
 body='\n'.join(method(s,a) for a in anchors)
 body=re.sub(r'app\.exteraless\.utils\.PredictiveBackAnimationHelper\s*\.getTransitionBackground','backgroundForGesture',body)
 body+='\n'+method(s,'    private void animateBackEndAnimation(')
 body+='\n'+method(s,'    private void startFlexyTimedLayoutAnimation(')
 a=s.index('    private final class InstantSlideTarget {');b=s.index('    private void clearInstantBackSeed()',a)
 body+='\n'+s[a:b]
 body=body.replace('ActionBarLayout','GestureOpeningProbe').replace('innerTranslationX;','inner;').replace('View.TRANSLATION_X','android.view.View.TRANSLATION_X')
 code=code.replace('int slideBegins;', 'int slideBegins;int customRequests;android.animation.Animator customSlide;boolean overrideSlide;boolean shouldOverrideSlideTransition(boolean a,boolean b){return overrideSlide;}android.animation.Animator getCustomSlideTransition(boolean a,boolean b,float d){customRequests++;return customSlide;}boolean isSupportEdgeToEdge(){return false;}java.util.ArrayList<AttachedSheet> sheetsStack;interface AttachedSheet{boolean attachedToParent();int getNavigationBarColor(int color);}')
 body+='''
 static final int BACK_ANIMATION_SPRING=1,BACK_ANIMATION_PREDICTIVE=2,BACK_ANIMATION_SLIDE=3;
 static class NaConfig {static int style=1;static final NaConfig INSTANCE=new NaConfig();final Field field=new Field();Field getBackAnimationStyle(){return field;}static class Field{int Int(){return style;}}}
 final android.view.animation.OvershootInterpolator overshootInterpolator=new android.view.animation.OvershootInterpolator();final android.view.animation.DecelerateInterpolator decelerateInterpolator=new android.view.animation.DecelerateInterpolator();\n boolean backAnimatorIsBack;android.app.Activity parentActivity;boolean m3PredictiveBack,predictiveBackLeft;float predictiveBackY;Object predictiveBackBackgroundDrawable;Animator backAnimator;VelocityTracker velocityTracker;int slideCompletions;boolean slideCancelled;
 final app.exteraless.utils.PredictiveBackAnimationHelper predictiveBackAnimation=new app.exteraless.utils.PredictiveBackAnimationHelper();
 BaseFragment getBackgroundFragment(){return fragmentsStack.get(fragmentsStack.size()-2);}
 void prepareForMoving(){startedTracking=true;containerViewBack.setVisibility(android.view.View.VISIBLE);}
 int backgroundRequests;Object backgroundForGesture(Object stack,Object fragment){backgroundRequests++;return new android.graphics.drawable.ColorDrawable(0xff333333);}float getPredictiveBackStartCornerRadius(){return 16;}static int dp(float value){return (int)value;}
 public void startTimedOpening(int style){startOpening(true);currentSpringAnimation.cancel();NaConfig.style=style;containerView.setScaleX(1);containerView.setScaleY(1);containerView.setTranslationY(0);containerView.setTranslationX(48);containerView.setAlpha(0);containerViewBack.setTranslationX(0);containerViewBack.setScaleX(1);containerViewBack.setScaleY(1);containerViewBack.setAlpha(1);startFlexyTimedLayoutAnimation(true,false);}
 void onSlideAnimationEnd(boolean revert){springRouteYRatio=0;springRouteBackgroundDrawable=null;slideCompletions++;slideCancelled=revert;if(!revert)fragmentsStack.remove(fragmentsStack.size()-1);startedTracking=false;animationInProgress=false;layoutToIgnore=null;containerView.setTranslationX(0);containerViewBack.setTranslationX(0);containerView.setScaleX(1);containerView.setScaleY(1);containerView.setTranslationY(0);inner=0;}
 '''
 code=code[:code.rfind('}')]+body+'\n}'
 put('GestureOpeningProbe.java',code)
 put('app/exteraless/utils/UtilsConfig.java','package app.exteraless.utils;public class UtilsConfig {public static float sensitivity=1;public static float adjustPredictiveBackProgress(float t){return Math.max(0,Math.min(1,t*sensitivity));}}')
