"""Explicit frame clock doubles; these tests do not measure Android/device FPS."""
from test_render_work_reuse import JAVA

ACTUAL=[JAVA/'app/exteraless/player/Spring.java',JAVA/'app/flexygram/bubbles/interaction/SelectedBubbleMotion.java']

def frames():
    return {
'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now=1000;public static long uptimeMillis(){return now;}}',
'android/view/Choreographer.java':'''package android.view;public class Choreographer{public interface FrameCallback{void doFrame(long t);}static final Choreographer c=new Choreographer();public FrameCallback pending;public static Choreographer getInstance(){return c;}public void postFrameCallback(FrameCallback f){if(pending!=null)throw new AssertionError("duplicate frame owner");pending=f;}public void removeFrameCallback(FrameCallback f){if(pending==f)pending=null;}public void frame(long t){android.os.SystemClock.now=t/1000000;FrameCallback f=pending;pending=null;if(f!=null)f.doFrame(t);}}''',
'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java':'package app.flexygram.bubbles.interaction;public class BubbleInteractionSettings{public static boolean enabled=true;public static boolean motionEnabled(){return enabled;}}'
    }
