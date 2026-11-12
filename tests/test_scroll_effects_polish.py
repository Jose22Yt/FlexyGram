"""Softer geometry, stable 3D projection and immediate interruption without blocking native input."""
from test_scroll_effects import SCROLL, controller_hosts
from test_render_work_reuse import probe


def test_all_intensity_levels_remain_visible_and_below_original_extremes(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectGeometry g=new ScrollEffectGeometry();
 for(float intensity:new float[]{.7f,1,1.3f}){
 g.calculate(1,1,400,800,1,1,intensity);check(Math.abs(g.rotationX)<56&&g.scaleX>.96&&Math.abs(g.translationY)<64);
 g.calculate(2,1,400,800,1,1,intensity);check(Math.abs(g.rotationX)<12&&Math.abs(g.rotationY)<6&&Math.abs(g.rotationZ)<1);
 g.calculate(3,1,400,800,1,1,intensity);check(Math.abs(g.translationX)<400*.16);
 }
 }}'''}, [SCROLL / 'ScrollEffectGeometry.java'])


def test_wheel_center_spacing_matches_its_actual_tilt_throughout_settling(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectGeometry g=new ScrollEffectGeometry();
 for(float level:new float[]{0,.00001f,.1f,.4f,.7f,1})for(float intensity:new float[]{.7f,1,1.3f})for(float p:new float[]{-.8f,-.4f,.1f,.4f,.8f}){
 g.calculate(1,p-.001f,400,800,level,1,intensity);float left=g.translationY;
 g.calculate(1,p+.001f,400,800,level,1,intensity);float right=g.translationY;
 g.calculate(1,p,400,800,level,1,intensity);double expected=Math.cos(Math.toRadians(g.rotationX));
 double actual=1+(right-left)/.002/400;check(Math.abs(expected-actual)<.002);
 check(Float.isFinite(g.translationY));
 }
 }}'''}, [SCROLL / 'ScrollEffectGeometry.java'])


def test_normal_rows_keep_the_same_pivot_when_crossing_the_viewport_edge(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.graphics.*;import android.os.SystemClock;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectsConfig.current=1;SystemClock.now=0;
 RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);c.beginFrame(100,900);c.onScrolled(list,0,80);
 SystemClock.now=60_000_000L;c.beginFrame(100,900);Canvas canvas=new Canvas();
 c.concat(canvas,99,139);check(Matrix.lastPreY==-119);
 c.concat(canvas,101,141);check(Matrix.lastPreY==-121);
 c.concat(canvas,0,800);float before=Matrix.lastPreY;
 c.concat(canvas,0,800.1f);check(Math.abs(Matrix.lastPreY-before)<.2f);
 c.concat(canvas,100,10000);check(Matrix.lastPreY==-500&&Camera.rotationX==0);
 }}'''
    probe(tmp_path, files, [SCROLL / n for n in ['ScrollEffectMotion.java', 'ScrollEffectGeometry.java', 'ScrollEffectsController.java']])


def test_touch_release_uses_the_displayed_pose_and_is_monotone_with_a_short_deadline(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){
 for(float sign:new float[]{-1,1}){ScrollEffectMotion m=new ScrollEffectMotion();m.scroll(80*sign,1000,0);
 m.advance(60_000_000L);float shown=m.amount(),direction=m.direction();
 m.scroll(-80*sign,1000,70_000_000L); // Input may be newer than the screen's last pose.
 m.interrupt(70_000_000L,shown,direction);check(m.amount()==shown&&m.direction()==direction);
 float previous=shown;
 for(long dt=1_000_000;dt<ScrollEffectMotion.TOUCH_RELEASE_NANOS;dt+=1_000_000){
 check(m.advance(70_000_000L+dt));check(m.amount()<=previous&&m.amount()>=0&&m.direction()==direction);previous=m.amount();}
 check(!m.advance(70_000_000L+ScrollEffectMotion.TOUCH_RELEASE_NANOS)&&m.amount()==0);
 for(int i=0;i<100;i++)check(!m.advance(1_000_000_000L+i));
 }
 }}'''}, [SCROLL / 'ScrollEffectMotion.java'])


def test_new_drag_can_resume_while_the_touch_release_is_still_running(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectMotion m=new ScrollEffectMotion();m.interrupt(0,.5f,1);
 m.advance(20_000_000L);float amount=m.amount();m.scroll(-20,1000,20_000_000L);check(m.amount()==amount);
 for(long t=30_000_000L;t<=100_000_000L;t+=10_000_000L){m.scroll(-20,1000,t);check(m.advance(t+1_000_000L));}
 check(m.amount()>0&&m.direction()<0); // Not locked until the old release's deadline.
 }}'''}, [SCROLL / 'ScrollEffectMotion.java'])


def test_same_timestamp_callbacks_are_coalesced_without_strength_kicks(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectMotion single=new ScrollEffectMotion(),batched=new ScrollEffectMotion();
 single.scroll(40,1000,0);for(int j=0;j<4;j++)batched.scroll(10,1000,0);
 for(int i=1;i<=60;i++){long t=i*8_000_000L;single.scroll(40,1000,t);
 for(int j=0;j<4;j++)batched.scroll(10,1000,t);
 single.advance(t+4_000_000L);batched.advance(t+4_000_000L);
 check(Math.abs(single.amount()-batched.amount())<.00001&&single.amount()<.90);
 check(Math.abs(single.direction()-batched.direction())<.00001);
 }
 }}'''}, [SCROLL / 'ScrollEffectMotion.java'])
