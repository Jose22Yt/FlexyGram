"""Regressions for the over-attenuated beta52 effect and blanket native-animation resets."""
from test_scroll_effects import SCROLL
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_each_selected_effect_is_present_during_a_short_slow_drag_at_every_level(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){for(float intensity:new float[]{.7f,1,1.3f}){
 ScrollEffectMotion motion=new ScrollEffectMotion();ScrollEffectGeometry geometry=new ScrollEffectGeometry();
 motion.scroll(3,800,0);
 for(long t=16_000_000L;t<=80_000_000L;t+=16_000_000L){motion.scroll(3,800,t);motion.advance(t);}
 check(motion.amount()>.5&&motion.amount()<.9);
 geometry.calculate(1,.8f,400,800,motion.amount(),motion.direction(),intensity);check(Math.abs(geometry.rotationX)>10);
 geometry.calculate(2,.8f,400,800,motion.amount(),motion.direction(),intensity);check(Math.abs(geometry.rotationX)>2);
 geometry.calculate(3,.8f,400,800,motion.amount(),motion.direction(),intensity);check(Math.abs(geometry.translationX)>12);
 motion.stop(90_000_000L);check(!motion.advance(2_000_000_000L));
 }} }'''}, [SCROLL / 'ScrollEffectMotion.java', SCROLL / 'ScrollEffectGeometry.java'])


def test_native_item_animation_and_detached_video_do_not_clear_the_entire_effect(tmp_path):
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    chat = method(chat[chat.index('chatListView = new ChatListRecyclerView'):], 'protected void dispatchDraw(Canvas canvas)')
    chat_prefix = chat[chat.index('{') + 1:chat.index('                drawLaterRoundProgressCell = null;')]
    home = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    home = method(home[home.index('    public class DialogsRecyclerView '):], 'protected void dispatchDraw(Canvas canvas)')
    home_prefix = home[home.index('{') + 1:home.index('            canvas.save();')]
    probe(tmp_path, {'Probe.java': '''class View{static final int VISIBLE=0;Object parent;int getVisibility(){return VISIBLE;}Object getParent(){return parent;}}
 class Animator{boolean isRunning(){return true;}}
 public class Probe{
 Object contentView=new Object(),scrimView,animationSupportListView;View videoPlayerContainer;
 int chatListViewPaddingTop=100,chatListViewPaddingVisibleOffset,blurredViewBottomOffset,scrollYOffset;
 float rightFragmentOpenedProgress;int resets,frames;
 int getHeight(){return 900;}int getPaddingTop(){return 100;}int getPaddingBottom(){return 0;}
 Animator getItemAnimator(){return new Animator();}boolean drawMovingViewsOverlayed(){return true;}
 void resetScrollEffects(){resets++;}void beginScrollEffectsFrame(float t,float b){frames++;}
 void chat(){CHAT}void home(){HOME}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();p.chat();check(p.resets==0&&p.frames==1);
 p.videoPlayerContainer=new View();p.chat();check(p.resets==0); // Retained VISIBLE, but removed from its parent.
 p.videoPlayerContainer.parent=p.contentView;p.chat();check(p.resets==1);
 p.videoPlayerContainer.parent=null;p.scrimView=new Object();p.chat();check(p.resets==2);
 p=new Probe();p.home();check(p.resets==0&&p.frames==1); // Native item animations may still be running.
 p.animationSupportListView=new Object();p.home();check(p.resets==1);
 p.animationSupportListView=null;p.rightFragmentOpenedProgress=.5f;p.home();check(p.resets==2);
 }}'''.replace('CHAT', chat_prefix).replace('HOME', home_prefix)})


def test_only_native_moving_rows_are_excluded_from_home_effect_and_hit_projection(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    actual = method(source[source.index('    public class DialogsRecyclerView '):], 'protected boolean getScrollEffectBounds(')
    probe(tmp_path, {'Probe.java': '''class View{}class RectF{}
 class DialogCell extends View{boolean moving;boolean isMoving(){return moving;}}
 class Base{int boundsCalls;protected boolean getScrollEffectBounds(View v,RectF b){boundsCalls++;return true;}}
 public class Probe extends Base{ACTUAL
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();DialogCell cell=new DialogCell();RectF b=new RectF();
 cell.moving=true;check(!p.getScrollEffectBounds(cell,b)&&p.boundsCalls==0);
 cell.moving=false;check(p.getScrollEffectBounds(cell,b)&&p.boundsCalls==1);
 check(!p.getScrollEffectBounds(new View(),b)&&p.boundsCalls==1);
 }}'''.replace('ACTUAL', actual)})
