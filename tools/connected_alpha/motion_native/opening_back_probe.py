"""Real Android containers/spring/coordinator and exact Back/completion bodies; fragments remain doubles."""
from player_probe import method
import sys

def write(put,root):
 sys.path.insert(0,str(root/'tools/connected_alpha'))
 from test_preview_navigation import fixture
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 code=fixture(s).replace('PreviewRegression','OpeningBackProbe')
 code=code.replace(method(code,' public static void main('),'').replace(method(code,' static OpeningBackProbe create('),'')
 container=method(code,' static class Container ')
 code=code.replace(container,'static class Container extends android.widget.FrameLayout {float x;Container(android.content.Context c){super(c);addView(new android.view.View(c),new android.widget.FrameLayout.LayoutParams(300,600));}public void setTranslationX(float value){x=value;super.setTranslationX(value);}}')
 code=code.replace(method(code,' static class SpringAnimation'), '')
 code=code.replace('import java.util.*;','import java.util.*;import app.flexygram.motion.SpringAnimation;')
 code=code.replace('Container containerView=new Container(),containerViewBack=new Container();','Container containerView,containerViewBack;')
 code=code.replace('void setAlpha(float f){}','public void setAlpha(float f){super.setAlpha(f);}')
 code=code.replace('public class OpeningBackProbe {','''public class OpeningBackProbe extends android.widget.FrameLayout {
 public Runnable afterOpen;
 public OpeningBackProbe(android.content.Context c){super(c);containerView=new Container(c);containerViewBack=new Container(c);addView(containerViewBack,new android.widget.FrameLayout.LayoutParams(300,600));addView(containerView,new android.widget.FrameLayout.LayoutParams(300,600));fragmentsStack.add(new BaseFragment());fragmentsStack.add(new ChatActivity());}
 public void startOpening(boolean timed){transitionAnimationInProgress=true;transitionAnimationStartTime=System.currentTimeMillis();onOpenAnimationEndRunnable=()->{if(afterOpen!=null)afterOpen.run();};currentSpringAnimation=new SpringAnimation(this,new androidx.dynamicanimation.animation.FloatValueHolder(0)).setSpring(new androidx.dynamicanimation.animation.SpringForce(1000));if(timed)currentSpringAnimation.setDuration(2000);currentSpringAnimation.start();}
 ''')
 put('OpeningBackProbe.java',code)
