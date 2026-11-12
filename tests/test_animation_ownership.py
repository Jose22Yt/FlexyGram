"""Run production animation ownership code; counted callbacks are not device FPS."""
from test_render_work_reuse import JAVA,probe
from test_composer_layout import method
from motion43_support import frames,ACTUAL


def test_bubble_tap_reset_replace_and_retarget_keep_one_frame_owner(tmp_path):
    probe(tmp_path,{
        'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now=1000;public static long uptimeMillis(){return now;}}',
        'android/view/View.java':'''package android.view;public class View{public Runnable pending,hook;public int posts,invalidates;public void postOnAnimation(Runnable r){if(pending!=null)throw new AssertionError("duplicate frame");pending=r;posts++;}public void removeCallbacks(Runnable r){if(pending==r)pending=null;}public void invalidate(){invalidates++;Runnable h=hook;hook=null;if(h!=null)h.run();}public void frame(){android.os.SystemClock.now+=16;Runnable r=pending;pending=null;if(r!=null)r.run();}}''',
        'Probe.java':'''import app.flexygram.bubbles.interaction.BubbleTapMotion;import android.view.View;
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}static void settle(View v){for(int i=0;i<200&&v.pending!=null;i++)v.frame();check(v.pending==null);}
 public static void main(String[]args){
 View v=new View();BubbleTapMotion m=new BubbleTapMotion(v);v.hook=m::reset;m.press(0,0,0);check(v.pending==null&&m.scale()==1);m.press(0,0,0);float scale=m.scaleX();int posts=v.posts;for(int i=0;i<1000;i++)m.press(0,0,0);check(m.scaleX()==scale&&v.posts==posts);
 v.hook=m::reset;v.frame();check(v.pending==null&&m.scale()==1&&!m.pressed());
 m.press(0,0,0);v.hook=()->{m.reset();m.press(0,0,0);};v.frame();check(v.pending!=null&&m.pressed());settle(v);check(m.pressed());
 posts=v.posts;int invalidates=v.invalidates;for(int i=0;i<1000;i++)m.drag(0,0,10);check(v.posts==posts&&v.invalidates==invalidates);
 m.reset();m.press(0,0,0);final boolean[]released={false};
 Runnable hook=new Runnable(){public void run(){if(m.scaleX()==.978f&&m.scaleY()==.965f){released[0]=true;m.release();}else v.hook=this;}};v.hook=hook;settle(v);check(released[0]&&!m.pressed()&&m.scale()==1);
 }}'''
    },[JAVA/'app/exteraless/player/Spring.java',JAVA/'app/flexygram/bubbles/interaction/DampedSpringCurve.java',JAVA/'app/flexygram/bubbles/interaction/BubbleTapMotion.java'])


def test_selection_cleanup_cannot_replace_a_newer_nested_selection(tmp_path):
    files=frames();files['Probe.java']='''import app.flexygram.bubbles.interaction.SelectedBubbleMotion;import android.view.Choreographer;
public class Probe{public static void main(String[]args){SelectedBubbleMotion m=new SelectedBubbleMotion();int[]newDraws={0},oldDraws={0},done={0};m.enter(()->{});m.close(()->{done[0]++;m.enter(()->newDraws[0]++,.98f,.97f);});m.enter(()->oldDraws[0]++);if(done[0]!=1||oldDraws[0]!=0||newDraws[0]!=1||m.scaleX()!=.98f||!m.isRunning())throw new AssertionError("stale enter replaced newer owner");Choreographer.getInstance().frame(1016000000L);if(newDraws[0]!=2||oldDraws[0]!=0)throw new AssertionError();m.reset();if(Choreographer.getInstance().pending!=null)throw new AssertionError("frame leaked");
 // A cleanup-only reset releases the old owner; it must not cancel the incoming selection.
 m.enter(()->{});m.close(m::reset);m.enter(()->oldDraws[0]++);if(oldDraws[0]!=1||!m.hasOwner()||!m.isRunning())throw new AssertionError("cleanup suppressed incoming gesture");m.reset();}}
''';probe(tmp_path,files,ACTUAL)


def test_mini_player_reversals_immediate_updates_and_late_callbacks_are_safe(tmp_path):
    source=(JAVA/'app/exteraless/player/PlayerMiniView.java').read_text()
    methods=method(source,'private void setShown(')+method(source,'private void cancelShowAnimation(')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
class Animator{}class AnimatorListenerAdapter{public void onAnimationEnd(Animator a){}}
class CubicBezierInterpolator{CubicBezierInterpolator(double a,double b,double c,double d){}}
class ValueAnimator extends Animator{
 interface Update{void run(ValueAnimator a);}Update update;AnimatorListenerAdapter listener;float from,to,value;static int instances;boolean canceled;static ValueAnimator ofFloat(float from,float to){ValueAnimator a=new ValueAnimator();a.from=from;a.value=from;a.to=to;instances++;return a;}
 void addUpdateListener(Update u){update=u;}void addListener(AnimatorListenerAdapter l){listener=l;}void setDuration(int d){}void setInterpolator(Object i){}Object getAnimatedValue(){return value;}
 void emit(float v){value=v;update.run(this);}void start(){emit(from);}void cancel(){canceled=true;if(listener!=null)listener.onAnimationEnd(this);}void end(){emit(to);if(listener!=null)listener.onAnimationEnd(this);}
}
public class Probe{boolean shown,attached=true;float showProgress;ValueAnimator showAnimator;int draws,offsets;Runnable callback;
 boolean isAttachedToWindow(){return attached;}void applyTransform(){draws++;}void notifyOffset(){offsets++;Runnable next=callback;callback=null;if(next!=null)next.run();}
 METHODS
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.setShown(true,true);ValueAnimator first=p.showAnimator;first.emit(.35f);int count=ValueAnimator.instances;for(int i=0;i<1000;i++)p.setShown(true,true);check(ValueAnimator.instances==count&&p.showAnimator==first);
 p.setShown(true,false);check(first.canceled&&p.showAnimator==null&&p.showProgress==1);int draws=p.draws,offsets=p.offsets;first.emit(.2f);first.end();check(p.showProgress==1&&p.draws==draws&&p.offsets==offsets);
 p.setShown(false,true);ValueAnimator closing=p.showAnimator;closing.emit(.6f);p.callback=()->p.setShown(true,true);closing.emit(.5f);ValueAnimator reopened=p.showAnimator;check(reopened!=closing&&p.showProgress==.5f);closing.end();check(p.showAnimator==reopened&&p.showProgress==.5f);reopened.end();check(p.showAnimator==null&&p.showProgress==1);
 p.setShown(false,true);ValueAnimator detached=p.showAnimator;p.cancelShowAnimation();draws=p.draws;detached.emit(.1f);check(p.showAnimator==null&&p.draws==draws);
 p.attached=false;p.setShown(false,true);check(p.showProgress==0&&p.showAnimator==null);
 }}'''.replace('METHODS',methods)},[])
