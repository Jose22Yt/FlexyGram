"""Run the real selected-message spring with deterministic 30/60/90/120 Hz frames."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_actual_menu_motion_has_small_steps_single_frame_owner_and_interruptible_cleanup(tmp_path):
    probe(tmp_path, {
        'android/os/SystemClock.java': 'package android.os;public class SystemClock{public static long now=1000;public static long uptimeMillis(){return now;}}',
        'android/view/Choreographer.java': '''package android.view;public class Choreographer{
 public interface FrameCallback{void doFrame(long t);}static final Choreographer instance=new Choreographer();public FrameCallback pending;
 public static Choreographer getInstance(){return instance;}public void postFrameCallback(FrameCallback c){if(pending!=null&&pending!=c)throw new AssertionError("multiple owners");pending=c;}
 public void removeFrameCallback(FrameCallback c){if(pending==c)pending=null;}
 public void frame(long nanos){android.os.SystemClock.now=nanos/1000000;FrameCallback c=pending;pending=null;if(c!=null)c.doFrame(nanos);}
}''',
        'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java': 'package app.flexygram.bubbles.interaction;public class BubbleInteractionSettings{public static boolean enabled=true;public static boolean motionEnabled(){return enabled;}}',
        'Probe.java': '''import app.flexygram.bubbles.interaction.*;import android.view.Choreographer;
public class Probe{
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){
  for(int hz:new int[]{30,60,90,120}){
   var motion=new SelectedBubbleMotion();int[] draws={0},done={0};long t=1000000000L;android.os.SystemClock.now=1000;
   motion.enter(()->draws[0]++);check(motion.panelScale()>=.94f&&motion.panelOffset()<=8);
   float previous=motion.panelScale();int frames=0;
   while(motion.isRunning()&&frames++<hz){int before=draws[0];t+=1000000000L/hz;Choreographer.getInstance().frame(t);
    check(draws[0]-before==1);check(Math.abs(motion.panelScale()-previous)<.045f);
    check(motion.progress()>=0&&motion.progress()<=1);previous=motion.panelScale();
   }
   check(!motion.isRunning()&&motion.panelScale()==1f&&frames<=hz/2);
   motion.close(()->done[0]++);t+=1000000000L/hz;Choreographer.getInstance().frame(t);
   motion.finishImmediately();motion.finishImmediately();check(done[0]==1&&!motion.hasOwner());
   check(Choreographer.getInstance().pending==null);
   motion.enter(()->draws[0]++);motion.close(()->done[0]++);motion.reset();check(done[0]==2);
   check(!motion.isRunning()&&Choreographer.getInstance().pending==null);
  }
  BubbleInteractionSettings.enabled=false;var motion=new SelectedBubbleMotion();motion.enter(()->{});
  check(!motion.isRunning()&&motion.progress()==1);motion.close();check(!motion.hasOwner());
 }
}'''
    }, [JAVA/'app/exteraless/player/Spring.java', JAVA/'app/flexygram/bubbles/interaction/SelectedBubbleMotion.java'])


def test_compact_popup_captures_once_before_show_and_does_not_create_a_second_clock():
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    assert 'if (!compactContext) updateScrimSourceBitmap();' in chat
    prep=method(chat,'private void prepareSignatureMenuScrim(')
    assert prep.count('captureMessageMenuBlur(generation)')==1
    assert 'if (SharedConfig.chatBlurEnabled())' in prep
    assert 'new Animator' not in prep and 'ValueAnimator.of' not in prep
    show=chat[chat.index('Runnable showMenu = () -> {',chat.index('final MessageObject signatureSelectedMessage')):]
    assert show.index('prepareSignatureMenuScrim(v)')<show.index('popupLayout.setAlpha(0f)')<show.index('scrimPopupWindow.showAtLocation')<show.index('selectedBubbleMotion.enter(')
    compact=show[:show.index('} else if (isReactionsAvailableFinal')]
    assert 'dimBehindView(v, true, true)' not in compact
    capture=method(chat,'private void captureMessageMenuBlur(')
    assert 'blurGeneration != scrimBlurGeneration' in capture
