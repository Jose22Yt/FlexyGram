"""Live gesture handlers: scrolling never starts the bubble's compatibility spring."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_live_cell_keeps_down_move_cancel_static_and_preserves_confirmed_tap(tmp_path):
    source = (JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    assert 'signatureTapMotion.press(' not in source
    methods = '\n'.join(method(source, name) for name in [
        'public boolean dispatchTouchEvent(MotionEvent event)',
        'public void signatureTapEvent(MotionEvent event)', 'public boolean isSignatureTap()',
        'public void finishSignatureCandidate()', 'public void cancelSignatureGesture()'])
    files = {
        'android/os/SystemClock.java': 'package android.os;public class SystemClock{public static long now=100;public static long uptimeMillis(){return now;}}',
        'android/view/ViewConfiguration.java': 'package android.view;public class ViewConfiguration{public static ViewConfiguration get(Object c){return new ViewConfiguration();}public int getScaledTouchSlop(){return 10;}public static int getLongPressTimeout(){return 500;}}',
        'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java': 'package app.flexygram.bubbles.interaction;public class BubbleInteractionSettings{public static boolean tapAnimation(Object c){return true;}}',
        'Probe.java': '''
class MotionEvent {
 static final int ACTION_DOWN=0,ACTION_UP=1,ACTION_MOVE=2,ACTION_CANCEL=3,ACTION_POINTER_DOWN=5,ACTION_POINTER_UP=6;
 final int a;final float x,y;MotionEvent(int a,float x,float y){this.a=a;this.x=x;this.y=y;}
 int getActionMasked(){return a;}float getX(){return x;}float getY(){return y;}
}
class Native {int nativeEvents;public boolean dispatchTouchEvent(MotionEvent e){nativeEvents++;return true;}}
public class Probe extends Native {
 static class Motion {boolean pressed;int starts;void press(){pressed=true;starts++;}void drag(float x,float y,float s){}void release(){pressed=false;}void reset(){pressed=false;}}
 static class Message {boolean preview;boolean isSponsored(){return false;}boolean isEphemeral(){return false;}}
 static class Delegate {boolean canPerformActions(){return true;}boolean hasSelectedMessages(){return false;}}
 static class Photo {boolean isInsideImage(float x,float y){return true;}}
 final Motion signatureTapMotion=new Motion();Message currentMessageObject=new Message();Delegate delegate=new Delegate();Photo photoImage=new Photo();
 boolean signatureTapEligible,signatureMediaPress,drawPhotoImage;
 float signatureTapX,signatureTapY,signatureTapPivotX,signatureTapPivotY;long signatureTapReleased,signatureTapStarted;
 Object getContext(){return this;}float getEventX(MotionEvent e){return e.x;}float getEventY(MotionEvent e){return e.y;}
 boolean isInsideBackground(float x,float y){return x>=0&&y>=0;}
 int getBackgroundDrawableLeft(){return 0;}int getBackgroundDrawableRight(){return 100;}
 int getBackgroundDrawableTop(){return 0;}int getBackgroundDrawableBottom(){return 48;}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 void down(){dispatchTouchEvent(new MotionEvent(0,20,20));signatureTapEligible=true;signatureTapStarted=android.os.SystemClock.now;}
 void event(int a,float x,float y){MotionEvent e=new MotionEvent(a,x,y);dispatchTouchEvent(e);signatureTapEvent(e);}
 public static void main(String[] args){Probe p=new Probe();
  for(int cancel:new int[]{MotionEvent.ACTION_CANCEL,MotionEvent.ACTION_POINTER_DOWN,MotionEvent.ACTION_POINTER_UP}){
   p.down();p.event(cancel,20,20);check(!p.isSignatureTap()&&!p.signatureTapMotion.pressed);
  }
  p.down();for(int i=0;i<5;i++)p.event(2,20+i,20+i);p.event(2,40,40);p.event(1,40,40);
  check(!p.isSignatureTap()&&p.signatureTapMotion.starts==0);
  p.down();android.os.SystemClock.now+=30;p.event(1,21,20);
  check(p.isSignatureTap()&&p.signatureTapMotion.starts==0);
  p.finishSignatureCandidate();check(!p.isSignatureTap());
  p.down();android.os.SystemClock.now+=501;p.event(1,20,20);check(!p.isSignatureTap());
  check(p.nativeEvents>10); // Native dispatch is never consumed/replayed by the observer.
 }
}'''.replace('METHODS', methods)
    }
    probe(tmp_path, files)
    chat = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    assert 'selectedBubbleMotion.enter(' in chat
    assert 'finalReactionsLayout.setSignatureMotionProgress(phase)' in chat
    # The actual confirmed-tap menu retains its local, preference-independent motion.
    motion = (JAVA/'app/flexygram/bubbles/interaction/SelectedBubbleMotion.java').read_text()
    assert 'FastMotionTiming' not in motion
