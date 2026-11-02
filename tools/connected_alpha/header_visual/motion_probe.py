"""Compile the exact production reaction-transition methods against Android animators.
Navigation/notification services remain explicit doubles; no device performance claim.
"""
from pathlib import Path

def write_probe(source,root):
 text=(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/ReactionsContainerLayout.java').read_text()
 methods=text[text.index('    private ObjectAnimator signatureTransitionAnimator;'):text.index('    public int getTotalWidth()')]
 detach=text.rindex('\n    protected void onDetachedFromWindow() {')
 cleanup=text[text.index('        cancelSignatureTransition();',detach):text.index('        super.onDetachedFromWindow();',detach)]
 code='''import android.animation.*;import android.content.Context;import android.view.*;import android.view.animation.OvershootInterpolator;
import org.telegram.ui.Components.CubicBezierInterpolator;
public class ReactionsMotionProbe extends View {
 public static class LocaleController {public static boolean isRTL;}
 public boolean mirrorX;
 private int dp(float value){return (int)Math.ceil(getResources().getDisplayMetrics().density*value);}
 public float transitionProgress=1f;boolean animatePopup;ValueAnimator pullingDownBackAnimator,cancelPressedAnimation;
 public static class Locker {public boolean held;public int locks,releases;public void lock(){held=true;locks++;}public void unlock(){if(held){held=false;releases++;}}}
 public final Locker notificationsLocker=new Locker();
 public static final android.util.Property<ReactionsMotionProbe,Float> TRANSITION_PROGRESS_VALUE=new android.util.Property<ReactionsMotionProbe,Float>(Float.class,"progress"){
 public Float get(ReactionsMotionProbe o){return o.transitionProgress;}public void set(ReactionsMotionProbe o,Float v){o.setTransitionProgress(v);}};
 public ReactionsMotionProbe(Context c){super(c);}public void setTransitionProgress(float p){transitionProgress=p;}
 public ObjectAnimator current(){return signatureTransitionAnimator;}public void detachNow(){onDetachedFromWindow();}
 @Override protected void onDetachedFromWindow(){'''+cleanup+'''super.onDetachedFromWindow();}
'''+methods+'}'
 (source/'ReactionsMotionProbe.java').write_text(code)
 template=Path(__file__).with_name('ReactionsMotionTest.java.in')
 (source/'ReactionsMotionTest.java').write_bytes(template.read_bytes())
