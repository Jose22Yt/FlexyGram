import app.flexygram.bubbles.interaction.*;
import android.view.*;
import android.os.SystemClock;

/** Actual production springs/controllers; frame delivery is an explicit host double. */
public class PhysicsProbe {
 static void require(boolean v,String m){if(!v)throw new AssertionError(m);}
 static void frame(double dt){SystemClock.now+=dt*1000;View.frame();Choreographer.frame((long)(SystemClock.now*1e6));}
 public static void main(String[] args){
  int samples=0;
  app.flexygram.animation.FastMotionTiming.setEnabled(false);
  SelectedBubbleMotion preferenceMotion=new SelectedBubbleMotion();preferenceMotion.enter(()->{},.978f,.965f,0f,0f);frame(1d/60);
  require(preferenceMotion.isRunning(),"Bubble motion must have its own smooth trajectory");
  app.flexygram.animation.FastMotionTiming.setEnabled(true);frame(1d/60);
  require(preferenceMotion.isRunning(),"Toggling reduced animations must not cut a running bubble trajectory");preferenceMotion.reset();
  // Byte-for-byte equivalent trajectories regardless of the global option or OS scale.
  float[] baseline=null;
  for(boolean reduced:new boolean[]{false,true})for(double osScale:new double[]{0,.01,.5,1,5}){
   app.flexygram.animation.FastMotionTiming.setEnabled(reduced);
   app.flexygram.animation.FastMotionTiming.setSystemScaleProvider(()->osScale);
   SelectedBubbleMotion menu=new SelectedBubbleMotion();BubbleTapMotion press=new BubbleTapMotion(new View());
   menu.enter(()->{},.978f,.965f,0f,0f);press.press(0,0,0);
   float[] trajectory=new float[120];
   for(int i=0;i<40;i++){
    if(i==8){menu.close();press.release();}
    frame(.016);trajectory[i*3]=menu.panelProgress();trajectory[i*3+1]=press.scaleX();trajectory[i*3+2]=press.scaleY();
   }
   if(baseline==null)baseline=trajectory;else for(int i=0;i<trajectory.length;i++)
    require(Math.abs(trajectory[i]-baseline[i])<.00001,"Reduce animations/OS scale changed bubble physics");
   menu.reset();press.reset();
  }
  for(int hz:new int[]{60,90,120,144}){
   SelectedBubbleMotion m=new SelectedBubbleMotion();
   m.enter(()->{},.978f,.965f,0f,0f);
   require(m.panelScale()==SelectedBubbleMotion.PANEL_START_SCALE,"Card must start its anchored expansion before the first frame");
   float peak=0f;double peakTime=0;int settledFrame=0;
   for(int i=1;i<=hz;i++){
    frame(1d/hz);
    float p=m.geometryProgress();
    if(p>peak){peak=p;peakTime=i/(double)hz;}
    require(m.progress()>=0&&m.progress()<=1,"Opacity/reveal escaped bounds");
    require(m.panelScale()>=SelectedBubbleMotion.PANEL_START_SCALE&&m.panelScale()<1.025f,"Card rebound too large");
    require(Math.abs(m.spatialOffset(-1000f,4f))<=1004.001f,"Tall preview crossed reaction gap");
    require(m.spatialOffset(0f,4f)==0f,"Stationary preview moved");
    if(!m.isRunning()&&settledFrame==0)settledFrame=i;
   }
   require(peak>1f&&peak<1.1f,"Bubble must retain its soft damped rebound");
   require(settledFrame>1,"Bubble must interpolate across frames even with reduced animations enabled");
   require(settledFrame>0&&settledFrame/(double)hz<.40,"Entry did not settle");
   require(m.panelScale()==1&&m.panelOffset()==0,"Entry did not restore final card");
   System.out.println("Trajectory "+hz+" Hz: peak="+peak+" at "+peakTime+"s; settled="+settledFrame/(double)hz+"s");
   m.reset();
  }
  for(int hz:new int[]{60,90,120,144})for(int hold:new int[]{1,2,4,12,60}){
   View owner=new View();BubbleTapMotion press=new BubbleTapMotion(owner);
   press.press(0,0,0);require(press.scaleX()<1&&press.scaleX()>.998,"Immediate response must be tiny and integrated");
   for(int i=0;i<hold;i++)frame(1d/hz);
   float beforeDrag=press.scaleX(),speedBeforeDrag=press.velocityX();
   press.drag(3f,4f,8f);require(press.scaleX()==beforeDrag&&press.velocityX()==speedBeforeDrag,"Drag reset state");
   frame(1d/hz);
   float sx=press.scaleX(),sy=press.scaleY(),vx=press.velocityX(),vy=press.velocityY();
   press.release();require(press.scaleX()==sx&&press.velocityX()==vx,"UP dropped live state");
   SelectedBubbleMotion menu=new SelectedBubbleMotion();final int[] redraw={0},done={0};
   menu.enter(()->redraw[0]++,sx,sy,vx,vy);press.reset();
   require(menu.scaleX()==sx&&menu.scaleY()==sy&&menu.velocityX()==vx&&menu.velocityY()==vy,"Handoff dropped position/velocity");
   for(int i=0;i<hold;i++)frame(1d/hz);
   float before=menu.scaleX(),momentum=menu.velocityX(),phase=menu.panelProgress();
   menu.close(()->done[0]++);
   require(menu.scaleX()==before&&menu.velocityX()==momentum&&menu.panelProgress()==phase,"Closing restarted motion");
   for(int i=0;i<hz*2;i++){
    frame(1d/hz);samples++;
    require(Float.isFinite(menu.scaleX())&&menu.scaleX()>.96&&menu.scaleX()<1.02,"Unbounded message geometry");
    require(menu.panelProgress()>-.1&&menu.panelProgress()<1.1,"Unbounded panel spring");
    float offset=menu.spatialOffset(-1000f,4f);
    require(offset>=-1004.001f&&offset<=4.001f,"Interrupted return escaped spatial rebound bounds");
   }
   require(done[0]==1&&!menu.isRunning()&&!menu.hasOwner(),"Close leaked owner/callback");
   require(menu.scaleX()==1&&menu.scaleY()==1&&menu.progress()==0,"Close did not restore geometry");
   int idle=redraw[0];for(int i=0;i<10;i++)frame(1d/hz);require(redraw[0]==idle,"Idle redraw loop");
  }
  for(int i=0;i<100;i++){
   SelectedBubbleMotion m=new SelectedBubbleMotion();int[] old={0},fresh={0},closed={0};
   m.enter(()->old[0]++,.98f,.97f,-.1f,-.2f);frame(.008);m.close(()->closed[0]++);m.reset();
   require(closed[0]==1,"Lifecycle reset stranded a closing popup");
   m.enter(()->fresh[0]++);int count=old[0];for(int j=0;j<100;j++)frame(.008);require(old[0]==count,"Stale menu invalidator");m.reset();
  }
  for(int hz:new int[]{60,90,120,144})for(int openedFrames:new int[]{1,4,12,60}) {
   SelectedBubbleMotion fast=new SelectedBubbleMotion();final int[] completed={0};
   fast.enter(()->{});
   for(int i=0;i<openedFrames;i++)frame(1d/hz);
   fast.close(()->completed[0]++);
   int frames=0;
   while(fast.hasOwner()&&frames<hz){frame(1d/hz);frames++;}
   require(frames<=Math.ceil(.260*hz)+1,"Bubble close exceeded its local 260ms bound");
   require(completed[0]==1&&!fast.isRunning(),"Close cleanup did not run exactly once");
   fast.enter(()->{});frame(1d/hz);fast.close(()->completed[0]++);
   fast.finishImmediately();
   require(completed[0]==2&&!fast.hasOwner()&&!fast.isRunning()&&fast.progress()==0,"New input did not finish return immediately");
   fast.finishImmediately();frame(1d/hz);
   require(completed[0]==2,"Interrupted owner called completion twice");
  }
  SelectedBubbleMotion reentrant=new SelectedBubbleMotion();int[] completions={0};
  reentrant.enter(()->{if(reentrant.isClosing())reentrant.finishImmediately();});
  reentrant.close(()->completions[0]++);reentrant.finishImmediately();reentrant.finishImmediately();
  require(completions[0]==1,"Reentrant close must release the owner exactly once");
  System.out.println("PASS production spring/controllers: 60/90/120/144 Hz, "+samples+" simulated frames; device NOT_TESTED");
 }
}
