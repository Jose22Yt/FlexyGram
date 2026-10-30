import app.flexygram.bubbles.interaction.*;
import android.view.*;
import android.os.SystemClock;

/** Actual production springs/controllers; frame delivery is an explicit host double. */
public class PhysicsProbe {
 static void require(boolean v,String m){if(!v)throw new AssertionError(m);}
 static void frame(double dt){SystemClock.now+=dt*1000;View.frame();Choreographer.frame((long)(SystemClock.now*1e6));}
 public static void main(String[] args){
  int samples=0;
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
  System.out.println("PASS production spring/controllers: 60/90/120/144 Hz, "+samples+" simulated frames; device NOT_TESTED");
 }
}
