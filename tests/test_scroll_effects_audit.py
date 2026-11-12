"""Execute production optimizations and input continuity; operation counts are not device FPS."""
from test_scroll_effects import SCROLL, controller_hosts
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_reversing_and_releasing_preserve_position_and_velocity(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){
 for(boolean reverse:new boolean[]{false,true}){
 ScrollEffectMotion m=new ScrollEffectMotion();m.scroll(60,1000,0);
 m.advance(59_990_000L);float left=m.direction(),leftAmount=m.amount();
 m.advance(60_000_000L);float at=m.direction(),atAmount=m.amount();
 if(reverse)m.scroll(-60,1000,60_000_000L);else m.stop(60_000_000L);
 check(at==m.direction()&&atAmount==m.amount());
 m.advance(60_010_000L);
 float leftVelocity=(at-left)/.00001f,rightVelocity=(m.direction()-at)/.00001f;
 float leftAmountVelocity=(atAmount-leftAmount)/.00001f,rightAmountVelocity=(m.amount()-atAmount)/.00001f;
 check(Math.abs(leftVelocity-rightVelocity)<.15f&&Math.abs(leftAmountVelocity-rightAmountVelocity)<.15f);
 check(!m.advance(1_000_000_000L)&&m.amount()==0);
 }
 }}'''}, [SCROLL / 'ScrollEffectMotion.java'])


def test_event_history_has_same_response_across_refresh_rates_and_dropped_frames(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;import java.util.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static float[] run(int hz){ScrollEffectMotion m=new ScrollEffectMotion();TreeSet<Long> times=new TreeSet<>();
 for(long t:new long[]{0,35,90,170,210,230,300,600})times.add(t*1_000_000L);
 if(hz>0)for(int i=1;i*1_000_000_000d/hz<600_000_000L;i++)times.add((long)(i*1_000_000_000d/hz));
 float[]out=new float[6];int at=0;
 for(long t:times){m.advance(t);
 if(t==0||t==35_000_000L||t==90_000_000L)m.scroll(30,1000,t);
 if(t==170_000_000L)m.scroll(-30,1000,t);if(t==210_000_000L)m.stop(t);
 if(t==230_000_000L||t==300_000_000L||t==600_000_000L){out[at++]=m.amount();out[at++]=m.direction();}}
 return out;}
 public static void main(String[]a){float[]reference=run(60);
 for(int hz:new int[]{120,144,0}){float[]v=run(hz);for(int i=0;i<v.length;i++)check(Math.abs(v[i]-reference[i])<.00001);}
 }}'''}, [SCROLL / 'ScrollEffectMotion.java'])


def test_projection_budget_and_frame_snapshot_remain_stable_during_new_input(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.os.SystemClock;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){
 for(int style=1;style<=3;style++){
 ScrollEffectsConfig.current=style;SystemClock.now=0;RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);
 c.beginFrame(100,900);c.onScrolled(list,0,120);SystemClock.now=60_000_000L;c.beginFrame(100,900);
 Canvas canvas=new Canvas();int before=Camera.builds,rotations=Camera.rotations,locations=Camera.locations;
 for(int pass=0;pass<6;pass++)for(int row=0;row<30;row++)c.concat(canvas,100+row*25,120+row*25);
 check(Camera.builds-before==(style==1?30:style==2?1:0));
 check(Camera.rotations-rotations==(style==1?30:style==2?3:0));
 check(Camera.locations-locations==(style==3?0:1));
 int allocations=Matrix.allocations,builds=Camera.builds;
 for(int pass=0;pass<100;pass++)for(int row=0;row<30;row++)c.concat(canvas,100+row*25,120+row*25);
 check(Matrix.allocations==allocations&&Camera.builds==builds);
 long displayedHash=c.renderHash();SystemClock.now=70_000_000L;c.onScrolled(list,0,-120);
 check(c.renderHash()==displayedHash);c.onTouchDown();check(c.renderHash()==displayedHash);
 float[]point=new float[2];int inversions=Matrix.inversions;
 for(int row=0;row<30;row++)check(c.mapTouch(200,500,100+row*25,120+row*25,point));
 if(style==2)check(Matrix.inversions-inversions==1);
 SystemClock.now=90_000_000L;c.beginFrame(100,900);check(c.renderHash()!=displayedHash);
 int invalidates=list.invalidates;c.onScrolled(list,20,0);check(list.invalidates==invalidates);
 }
 }}'''
    probe(tmp_path, files, [SCROLL / n for n in ['ScrollEffectMotion.java', 'ScrollEffectGeometry.java', 'ScrollEffectsController.java']])


def test_lateral_hit_projection_uses_inverse_translation_and_resets_between_frames(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.os.SystemClock;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectsConfig.current=3;SystemClock.now=0;
 RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);c.beginFrame(100,900);c.onScrolled(list,0,100);
 SystemClock.now=60_000_000L;c.beginFrame(100,900);Canvas canvas=new Canvas();c.concat(canvas,850,890);
 float[]p=new float[2];check(c.mapTouch(200,870,850,890,p));check(p[0]<195&&p[0]>140&&p[1]==870);
 float before=p[0];SystemClock.now=100_000_000L;c.beginFrame(100,900);check(c.mapTouch(200,870,850,890,p)&&p[0]!=before);
 c.reset();check(!c.mapTouch(200,870,850,890,p));
 }}'''
    probe(tmp_path, files, [SCROLL / n for n in ['ScrollEffectMotion.java', 'ScrollEffectGeometry.java', 'ScrollEffectsController.java']])


def test_album_bounds_are_resolved_once_and_invalidate_on_native_geometry_changes(tmp_path):
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    start = source.index('    private abstract class ChatListRecyclerView ')
    fields_and_hooks = source[source.index('{', start) + 1:source.index('        public ChatListRecyclerView(', start)]
    bounds = method(source[start:], 'protected boolean getScrollEffectBounds(')
    probe(tmp_path, {'Probe.java': '''class RectF{float top,bottom;}
 class MessageObject{static class GroupedMessages{}}
 class View{float y;int height=24;float getY(){return y;}int getHeight(){return height;}}
 class ChatMessageCell extends View{MessageObject.GroupedMessages group;MessageObject.GroupedMessages getCurrentMessagesGroup(){return group;}}
 class ChatActionCell extends View{}class ChatMessageUnsupportedCell extends View{}
 class Base{View[]children;int reads;int getChildCount(){return children.length;}View getChildAt(int i){reads++;return children[i];}
 protected boolean getScrollEffectBounds(View v,RectF b){b.top=v.y;b.bottom=v.y+v.height;return true;}
 public void beginScrollEffectsFrame(float t,float b){}public void onScrolled(int dx,int dy){}protected void onLayout(boolean c,int l,int t,int r,int b){}protected void onDetachedFromWindow(){}
 }
 public class Probe extends Base{
 ACTUAL
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();p.children=new View[30];RectF b=new RectF();
 MessageObject.GroupedMessages group=null;
 for(int i=0;i<30;i++){if(i%3==0)group=new MessageObject.GroupedMessages();ChatMessageCell c=new ChatMessageCell();c.y=100+i*24;c.group=group;p.children[i]=c;}
 for(int pass=0;pass<6;pass++)for(int i=0;i<30;i++){
 p.getScrollEffectBounds(p.children[i],b);check(b.top==100+(i/3)*72&&b.bottom==172+(i/3)*72);}
 check(p.reads==300);Object cache=p.scrollEffectGroups;
 for(View v:p.children)v.y+=50;p.onScrolled(0,50);p.getScrollEffectBounds(p.children[0],b);check(b.top==150&&b.bottom==222);
 p.children[0].height=400;p.onLayout(true,0,0,400,900);p.getScrollEffectBounds(p.children[1],b);check(b.top==150&&b.bottom==550);
 p.beginScrollEffectsFrame(100,900);check(p.scrollEffectGroupCount==0&&p.scrollEffectGroups==cache);
 p.children=new View[40];for(int i=0;i<40;i++){ChatMessageCell c=new ChatMessageCell();c.y=i*24;c.group=new MessageObject.GroupedMessages();p.children[i]=c;}
 for(View v:p.children){p.getScrollEffectBounds(v,b);check(b.top==v.y&&b.bottom==v.y+24);}check(p.scrollEffectGroupCount==32);
 p.onDetachedFromWindow();check(p.scrollEffectGroupCount==0);for(Object key:p.scrollEffectGroups)check(key==null);
 }}'''.replace('ACTUAL', fields_and_hooks + bounds)})


def test_motion_math_does_not_allocate_per_frame_after_warmup(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;import java.lang.management.ManagementFactory;
 public class Probe{
 static void frames(ScrollEffectMotion m,ScrollEffectGeometry g,int start,int count){
 for(int i=start;i<start+count;i++){long now=i*8_000_000L;m.scroll(i%120<60?20:-20,1000,now);m.advance(now+4_000_000L);
 for(int style=1;style<=3;style++)g.calculate(style,.8f,400,1000,m.amount(),m.direction(),1);}}
 public static void main(String[]a){
 com.sun.management.ThreadMXBean bean=(com.sun.management.ThreadMXBean)ManagementFactory.getThreadMXBean();
 if(!bean.isThreadAllocatedMemorySupported())return;bean.setThreadAllocatedMemoryEnabled(true);
 ScrollEffectMotion m=new ScrollEffectMotion();ScrollEffectGeometry g=new ScrollEffectGeometry();frames(m,g,0,20000);
 long thread=Thread.currentThread().threadId();long before=bean.getThreadAllocatedBytes(thread);
 frames(m,g,20000,20000);long bytes=bean.getThreadAllocatedBytes(thread)-before;
 if(bytes>4096)throw new AssertionError("Unexpected frame allocation: "+bytes);
 }}'''}, [SCROLL / 'ScrollEffectMotion.java', SCROLL / 'ScrollEffectGeometry.java'])
