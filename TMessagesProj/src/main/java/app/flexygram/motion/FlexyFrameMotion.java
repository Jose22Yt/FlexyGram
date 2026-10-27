/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;
import android.os.Looper;
import android.view.Choreographer;
import android.view.View;
import java.util.ArrayList;
import java.util.WeakHashMap;

/** Single application-local Choreographer clock. No ValueAnimator/ObjectAnimator scale dependency. */
public final class FlexyFrameMotion implements View.OnAttachStateChangeListener {
    public interface Listener {void onValue(float value);}
    private static final ArrayList<FlexyFrameMotion> active=new ArrayList<>();
    private static final WeakHashMap<FlexyFrameMotion,Boolean> instances=new WeakHashMap<>();
    private static FlexyFrameMotion[] batch=new FlexyFrameMotion[16];
    private static boolean posted,ticking;
    private static final Choreographer.FrameCallback CLOCK=FlexyFrameMotion::frame;
    private final View owner;private final Listener listener;private final FlexyMotionSpring spring;
    private float speedMultiplier=1;
    public void setSpeedMultiplier(float value){checkMain();if(!Float.isFinite(value)||value<.1f||value>10)throw new IllegalArgumentException("speed");speedMultiplier=value;}
    private boolean timed;private float timedStart,timedTarget;private double timedElapsed,timedDuration;
    private long previousFrameNanos;private boolean running,disposed;private Runnable end;private Runnable configurationChanged;private long generation;
    public FlexyFrameMotion(View owner,float initial,Listener listener){
        this(owner,initial,listener,.0006f,.004f);
    }
    public FlexyFrameMotion(View owner,float initial,Listener listener,float positionThreshold,float velocityThreshold){
        checkMain();if(owner==null||listener==null)throw new IllegalArgumentException("owner/listener");this.owner=owner;this.listener=listener;spring=new FlexyMotionSpring(initial);spring.thresholds(positionThreshold,velocityThreshold);owner.addOnAttachStateChangeListener(this);instances.put(this,Boolean.TRUE);
    }
    private static void checkMain(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("main thread");}
    public float current(){return spring.value();}
    public boolean isRunning(){return running;}
    public void animateTo(float target){animateTo(target,null);}
    public void animateTo(float target,Runnable completion){
        checkMain();if(disposed)return;timed=false;generation++;end=completion;spring.target(target);FlexyMotionSettings.State s=FlexyMotionSettings.state(owner.getContext());
        if(s.instant()||!visible()){completeInstant();return;}
        spring.configure(s.stiffness,s.damping);
        if(spring.settled()){completeInstant();return;}
        if(!running){running=true;previousFrameNanos=System.nanoTime();active.add(this);}post();
    }
    /** Linear timeline on the same coordinator; native curves are applied by the listener. */
    public void animateTimedTo(float target,long durationMillis,Runnable completion) {
        checkMain();if(disposed)return;if(durationMillis<0)throw new IllegalArgumentException("duration");
        generation++;end=completion;timed=true;timedStart=spring.value();timedTarget=target;timedElapsed=0;timedDuration=durationMillis/1000.0;spring.target(target);
        FlexyMotionSettings.State s=FlexyMotionSettings.state(owner.getContext());
        if(s.instant()||durationMillis==0||!visible()||timedStart==target){completeInstant();return;}
        if(!running){running=true;previousFrameNanos=System.nanoTime();active.add(this);}post();
    }
    private boolean visible(){return owner.isAttachedToWindow()&&owner.getWindowVisibility()==View.VISIBLE&&owner.isShown();}
    public void snapTo(float value){checkMain();if(disposed)return;generation++;end=null;stop();spring.snapTo(value);listener.onValue(value);}
    public void cancel(){checkMain();generation++;stop();end=null;}
    public void dispose(){checkMain();if(disposed)return;cancel();disposed=true;configurationChanged=null;instances.remove(this);owner.removeOnAttachStateChangeListener(this);}
    private void stop(){if(running){running=false;active.remove(this);}previousFrameNanos=0;if(active.isEmpty()&&posted){Choreographer.getInstance().removeFrameCallback(CLOCK);posted=false;}}
    private void completeInstant(){long ticket=generation;float value=spring.target();stop();spring.snapTo(value);listener.onValue(value);if(ticket==generation)finish();}
    private void finish(){Runnable r=end;end=null;if(r!=null)r.run();}
    private static void post(){if(!posted&&!ticking&&!active.isEmpty()){posted=true;Choreographer.getInstance().postFrameCallback(CLOCK);}}
    private static void frame(long frameTimeNanos){
        posted=false;ticking=true;int n=active.size();if(batch.length<n)batch=new FlexyFrameMotion[Math.max(n,batch.length*2)];active.toArray(batch);
        try{for(int i=0;i<n;i++){FlexyFrameMotion motion=batch[i];batch[i]=null;if(motion!=null&&motion.running&&!motion.disposed)motion.step(frameTimeNanos);}}
        finally{for(int i=0;i<n;i++)batch[i]=null;ticking=false;post();}
    }
    private void step(long frameTimeNanos){
        if(!visible()){completeInstant();return;}
        FlexyMotionSettings.State s=FlexyMotionSettings.state(owner.getContext());
        if(s.instant()){completeInstant();return;}
        spring.configure(s.stiffness,s.damping);long delta=Math.max(0,frameTimeNanos-previousFrameNanos);previousFrameNanos=Math.max(previousFrameNanos,frameTimeNanos);
        long ticket=generation;float value;boolean settled;
        if(timed){
            timedElapsed+=delta*1e-9*s.speed*speedMultiplier/s.profile.timelineScale;
            double fraction=Math.min(1,timedElapsed/timedDuration);settled=fraction>=1;
            value=timedStart+(timedTarget-timedStart)*(float)fraction;
            float velocity=settled?0:(timedTarget-timedStart)*s.speed*speedMultiplier/(float)(timedDuration*s.profile.timelineScale);
            spring.state(value,velocity,timedTarget);
        }else{value=spring.advance(delta*1e-9f*s.speed*speedMultiplier);settled=spring.settled();}
        if(settled)stop();listener.onValue(value);if(settled&&!running&&ticket==generation)finish();
    }
    public void setOnSettingsChanged(Runnable listener){checkMain();configurationChanged=listener;}
    static void settingsChanged(){
        checkMain(); // rare settings event; allocation is outside the frame loop
        for(FlexyFrameMotion motion:instances.keySet().toArray(new FlexyFrameMotion[0]))if(motion!=null&&!motion.disposed){if(motion.configurationChanged!=null)motion.configurationChanged.run();if(motion.disposed)continue;FlexyMotionSettings.State s=FlexyMotionSettings.state(motion.owner.getContext());if(s.instant()){motion.completeInstant();}else motion.spring.configure(s.stiffness,s.damping);}
    }
    public static int activeCount(){checkMain();return active.size();}
    @Override public void onViewAttachedToWindow(View v){}
    @Override public void onViewDetachedFromWindow(View v){cancel();}
}
