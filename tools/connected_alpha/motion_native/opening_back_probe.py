"""Exact Back/completion and standard renderer with real containers/springs; fragment transactions are doubles."""
from player_probe import method
import sys

def write(put,root):
 sys.path.insert(0,str(root/'tools/connected_alpha'))
 from test_preview_navigation import fixture
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 code=fixture(s).replace('PreviewRegression','OpeningBackProbe')
 code=code.replace(method(code,' public static void main('),'').replace(method(code,' static OpeningBackProbe create('),'')
 container=method(code,' static class Container ')
 code=code.replace(container,'static class Container extends android.widget.FrameLayout {boolean isKeyboardVisible;float x;Container(android.content.Context c){super(c);addView(new android.view.View(c),new android.widget.FrameLayout.LayoutParams(300,600));}public void setTranslationX(float value){x=value;super.setTranslationX(value);}}')
 code=code.replace(method(code,' static class SpringAnimation'), '')
 code=code.replace('import java.util.*;','import java.util.*;import app.flexygram.motion.SpringAnimation;import androidx.dynamicanimation.animation.*;import androidx.core.math.MathUtils;import androidx.core.graphics.ColorUtils;import org.telegram.ui.ActionBar.Theme;')
 code=code.replace('Container containerView=new Container(),containerViewBack=new Container();','Container containerView,containerViewBack;')
 code=code.replace('void setAlpha(float f){}','public void setAlpha(float f){super.setAlpha(f);}')
 code=code.replace('Object layoutToIgnore,springRouteBackgroundDrawable,previewMenu;','Object layoutToIgnore,springRouteBackgroundDrawable;android.view.View previewMenu;')
 code=code.replace('previewMenu=new Object();','previewMenu=new android.view.View(getContext());')
 code=code.replace('static class AndroidUtilities{','static class AndroidUtilities{static int dp(float v){return (int)v;}static float lerp(float a,float b,float t){return a+(b-a)*t;}')
 code=code.replace('Dialog dialog;boolean sheet,allowBack=true;','Runnable onProgress;int updates;float progress;void onTransitionAnimationProgress(boolean open,float v){updates++;progress=v;if(onProgress!=null)onProgress.run();}Integer getNavigationBarColor(){return 0xff333333;}void setNavigationBarColor(int c){}Dialog dialog;boolean sheet,allowBack=true;')
 start=s.index('    private void startLayoutAnimation(')
 a=s.index('            currentSpringAnimation = createInstantLayoutSpring(',start)
 b=s.index('            currentSpringAnimation.start();',a)
 spring=s[a:b]+'currentSpringAnimation.start();'
 code=code.replace(method(code,'void beginClose('),'''void beginClose(BaseFragment target){closeRequests++;transitionAnimationStartTime=System.currentTimeMillis();transitionAnimationInProgress=true;layoutToIgnore=containerView;Container temp=containerView;containerView=containerViewBack;containerViewBack=temp;newFragment=fragmentsStack.get(0);oldFragment=target;onCloseAnimationEndRunnable=()->{fragmentsStack.remove(target);inPreviewMode=false;previewMenu=null;};startNativeSpring(false,false);}''')
 code=code.replace('public class OpeningBackProbe {','''public class OpeningBackProbe extends android.widget.FrameLayout {
 static final float SPRING_STIFFNESS=900,SPRING_STIFFNESS_PREVIEW=650,SPRING_STIFFNESS_PREVIEW_OUT=800;
 float animationProgress;final android.graphics.drawable.ColorDrawable previewBackgroundDrawable=new android.graphics.drawable.ColorDrawable();
 public Runnable afterOpen;
 public OpeningBackProbe(android.content.Context c){super(c);containerView=new Container(c);containerViewBack=new Container(c);addView(containerViewBack,new android.widget.FrameLayout.LayoutParams(300,600));addView(containerView,new android.widget.FrameLayout.LayoutParams(300,600));fragmentsStack.add(new BaseFragment());fragmentsStack.add(new ChatActivity());}
 public void startOpening(boolean timed){USE_SPRING_ANIMATION=!timed;USE_ACTIONBAR_CROSSFADE=true;transitionAnimationInProgress=true;transitionAnimationStartTime=System.currentTimeMillis();newFragment=getLastFragment();oldFragment=fragmentsStack.get(0);onOpenAnimationEndRunnable=()->{if(afterOpen!=null)afterOpen.run();};containerView.setTranslationX(getWidth());containerView.setScaleX(.85f);containerView.setScaleY(.85f);if(timed){currentSpringAnimation=new SpringAnimation(this,new FloatValueHolder(0)).setSpring(new SpringForce(1000)).setDuration(2000);currentSpringAnimation.start();}else startNativeSpring(true,false);}
 '''+method(s,'    private SpringAnimation createInstantLayoutSpring(')+'\n'+'void startNativeSpring(boolean open,boolean preview){'+spring+'}')
 code=code[:code.rfind('}')]+'void setInstantRevealTranslationX(android.view.View surface,float x){surface.setTranslationX(x);}' +code[code.rfind('}'):]
 put('OpeningBackProbe.java',code)
