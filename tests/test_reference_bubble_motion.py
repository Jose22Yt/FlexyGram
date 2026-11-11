"""Reference-style menu geometry, actual elapsed-time integration and guarded blur publication."""
from test_render_work_reuse import JAVA,probe
from test_composer_layout import method
from motion43_support import frames,ACTUAL


def test_exact_spring_preserves_elapsed_time_across_rates_and_irregular_frames(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.exteraless.player.Spring;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}static Spring create(float damping){Spring s=new Spring(.978f,640f,damping,.00000001f);s.setState(.978f,-.08f);s.target=1.012f;return s;}
 public static void main(String[]args){for(float damping:new float[]{.55f,.82f,1f,1.4f}){
  Spring reference=create(damping);reference.stepExact(.2f);
  for(int hz:new int[]{30,60,90,120,144,240}){Spring s=create(damping);double elapsed=0;while(elapsed<.2-1e-10){double dt=Math.min(1d/hz,.2-elapsed);s.stepExact((float)dt);elapsed+=dt;}check(Math.abs(s.value-reference.value)<.000003&&Math.abs(s.velocity()-reference.velocity())<.00002);}
  Spring irregular=create(damping);for(float dt:new float[]{.007f,.026f,.009f,.083f,.075f})irregular.stepExact(dt);check(Math.abs(irregular.value-reference.value)<.000003);
  float position=irregular.value,speed=irregular.velocity();irregular.target=.99f;check(irregular.value==position&&irregular.velocity()==speed);
  irregular.stepExact(0);irregular.stepExact(Float.NaN);check(irregular.value==position&&irregular.velocity()==speed);irregular.stepExact(2);check(Float.isFinite(irregular.value)&&Float.isFinite(irregular.velocity()));
 }} }'''},[JAVA/'app/exteraless/player/Spring.java'])


def test_late_blur_fades_from_zero_without_restarting_message_geometry(tmp_path):
    files=frames();files['Probe.java']='''import app.flexygram.bubbles.interaction.*;import android.view.Choreographer;public class Probe{
 static long time=1000000000L;static void frame(){time+=16666667L;Choreographer.getInstance().frame(time);}static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){var m=new SelectedBubbleMotion();m.enter(()->{});check(m.backdropProgress()==0&&m.panelScale()==SelectedBubbleMotion.PANEL_START_SCALE);
 for(int i=0;i<30;i++){frame();check(m.backdropProgress()==0);}check(!m.isRunning()&&m.hasOwner()&&m.scaleX()==SelectedBubbleMotion.OPEN_MESSAGE_SCALE);
 float scale=m.scaleX();m.backdropReady();check(m.backdropProgress()==0&&m.scaleX()==scale&&m.isRunning());m.backdropReady();frame();check(m.backdropProgress()>0&&m.backdropProgress()<.3f);
 float previous=m.backdropProgress();for(int i=0;i<30;i++){frame();check(m.backdropProgress()>=previous&&m.backdropProgress()<=1);previous=m.backdropProgress();}
 check(!m.isRunning()&&m.backdropProgress()==1&&m.scaleX()==scale&&Choreographer.getInstance().pending==null);
 int[]done={0};m.close(()->done[0]++);for(int i=0;i<30;i++)frame();check(!m.hasOwner()&&done[0]==1&&Choreographer.getInstance().pending==null);m.backdropReady();check(!m.isRunning()&&Choreographer.getInstance().pending==null);
 BubbleInteractionSettings.enabled=false;m.enter(()->{});m.backdropReady();check(m.progress()==1&&m.backdropProgress()==1&&!m.isRunning());m.close();check(!m.hasOwner());
 }}''';probe(tmp_path,files,ACTUAL)


def test_selected_message_and_panel_share_the_same_trajectory_at_each_refresh_rate(tmp_path):
    files=frames();files['Probe.java']='''import app.flexygram.bubbles.interaction.*;import android.view.Choreographer;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){float position=0,scale=0,speed=0;for(int hz:new int[]{30,60,90,120,144,240}){
 android.os.SystemClock.now=1000;var m=new SelectedBubbleMotion();m.enter(()->{});long end=1200000000L,last=1000000000L;
 for(int i=1;last<end;i++){last=Math.min(end,1000000000L+Math.round(i*1000000000d/hz));Choreographer.getInstance().frame(last);}
 if(hz==30){position=m.panelProgress();scale=m.scaleX();speed=m.velocityX();}else check(Math.abs(m.panelProgress()-position)<.00001f&&Math.abs(m.scaleX()-scale)<.00001f&&Math.abs(m.velocityX()-speed)<.00002f);
 check(m.panelScale()<=1.025f&&m.scaleX()<=1.02f&&Math.abs(m.spatialOffset(-1000,4))<=1004.001f);
 float before=m.scaleX(),velocity=m.velocityX(),phase=m.panelProgress();m.close();check(m.scaleX()==before&&m.velocityX()==velocity&&m.panelProgress()==phase);m.finishImmediately();check(Choreographer.getInstance().pending==null);
 }
 android.os.SystemClock.now=1000;var early=new SelectedBubbleMotion();early.enter(()->{});Choreographer.getInstance().frame(999000000L);check(early.panelProgress()==0);Choreographer.getInstance().frame(1016000000L);float phase=early.panelProgress();early.finishImmediately();
 android.os.SystemClock.now=1000;var normal=new SelectedBubbleMotion();normal.enter(()->{});Choreographer.getInstance().frame(1016000000L);check(Math.abs(normal.panelProgress()-phase)<.000001f);normal.finishImmediately();
 } }''';probe(tmp_path,files,ACTUAL)


def test_inline_capture_is_kept_and_stale_or_closing_capture_is_discarded(tmp_path):
    source=(JAVA/'org/telegram/ui/ChatActivity.java').read_text();capture=method(source,'private void captureMessageMenuBlur(')
    files=frames();files['Probe.java']='''import app.flexygram.bubbles.interaction.*;public class Probe{
 static class Bitmap{boolean recycled;void recycle(){recycled=true;}}static class Shader{enum TileMode{CLAMP}}static class BitmapShader extends Shader{BitmapShader(Bitmap b,TileMode x,TileMode y){}}
 static class Paint{static final int ANTI_ALIAS_FLAG=1;Paint(int f){}void setShader(Shader s){}}static class Matrix{}
 static class View{boolean attached=true;int invalidations;boolean isAttachedToWindow(){return attached;}void invalidate(){invalidations++;}}
 static class Source{Bitmap value;void setBitmap(Bitmap b){value=b;}}static class Factory{void invalidateAllLinkedViews(){}}static class Blur3Utils{static void checkBitmapSourceMatrixScale(Source s,View v){}}
 static class ScrimOptions{interface Result{void run(Bitmap a,Bitmap b);}static boolean async;static Result pending;static Bitmap lastA,lastB;static void makeGlobalBlurBitmaps(Result cb,boolean mode){if(async)pending=cb;else deliver(cb);}static void deliver(Result cb){lastA=new Bitmap();lastB=new Bitmap();cb.run(lastA,lastB);}static void complete(){Result cb=pending;pending=null;deliver(cb);}}
 int scrimBlurGeneration=7;Object scrimPopupWindow=new Object();View fragmentView=new View(),scrimView=new View(),contentView=new View();Bitmap scrimBlurBitmap;Paint scrimBlurBitmapPaint;BitmapShader scrimBlurBitmapShader;Matrix scrimBlurMatrix;Source scrimBlur3SourceBitmap=new Source();Factory scrimBlur3Factory=new Factory();SelectedBubbleMotion selectedBubbleMotion=new SelectedBubbleMotion();
 CAPTURE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.captureMessageMenuBlur(7,true);check(p.scrimBlurBitmap!=null&&!p.scrimBlurBitmap.recycled&&!p.selectedBubbleMotion.hasOwner());
 p.selectedBubbleMotion.enter(()->{});if(p.scrimBlurBitmap!=null)p.selectedBubbleMotion.backdropReady();check(p.selectedBubbleMotion.backdropProgress()==0&&p.selectedBubbleMotion.isRunning());
 Bitmap published=p.scrimBlurBitmap;ScrimOptions.async=true;p.captureMessageMenuBlur(7,true);p.scrimBlurGeneration=8;ScrimOptions.complete();check(ScrimOptions.lastA.recycled&&ScrimOptions.lastB.recycled&&!published.recycled);
 p.captureMessageMenuBlur(8,true);p.selectedBubbleMotion.close();ScrimOptions.complete();check(ScrimOptions.lastA.recycled&&ScrimOptions.lastB.recycled&&!published.recycled);p.selectedBubbleMotion.finishImmediately();
 p.scrimPopupWindow=null;p.captureMessageMenuBlur(8,true);ScrimOptions.complete();check(ScrimOptions.lastA.recycled&&ScrimOptions.lastB.recycled);
 }}'''.replace('CAPTURE',capture);probe(tmp_path,files,ACTUAL)
