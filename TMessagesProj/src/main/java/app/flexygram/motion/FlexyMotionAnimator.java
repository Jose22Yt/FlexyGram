/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.animation.Animator;
import android.animation.TimeInterpolator;
import android.os.Looper;
import android.os.Handler;
import android.view.View;
import android.view.animation.AccelerateDecelerateInterpolator;
import java.util.ArrayList;

/** Standalone listener-compatible migration adapter; never place inside AnimatorSet.
 * Time comes exclusively from FlexyFrameMotion. No ValueAnimator/Android animation handler.
 * Keeps native transition curves and their completion/cancel contracts on the shared clock.
 */
public final class FlexyMotionAnimator extends Animator implements View.OnAttachStateChangeListener {
    private static final Handler UI=new Handler(Looper.getMainLooper());
    private boolean detachedPending;
    private final Runnable detachedCleanup=()->{detachedPending=false;finish(true,false);};
    private final View owner;
    private final float from,to;
    private final FlexyFrameMotion.Listener property;
    private TimeInterpolator curve=new AccelerateDecelerateInterpolator();
    private FlexyFrameMotion frames;
    private long duration=300;
    private boolean running,paused;
    private float fraction;
    private ArrayList<AnimatorPauseListener> pauseListeners;

    public FlexyMotionAnimator(View owner,float from,float to,FlexyFrameMotion.Listener property){
        if(owner==null||property==null||!Float.isFinite(from)||!Float.isFinite(to))throw new IllegalArgumentException("animation");
        this.owner=owner;this.from=from;this.to=to;this.property=property;
    }
    private static void main(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("main thread");}
    @Override public FlexyMotionAnimator setDuration(long millis){if(millis<0)throw new IllegalArgumentException("duration");duration=millis;return this;}
    @Override public long getDuration(){return duration;}
    @Override public long getStartDelay(){return 0;}
    @Override public void setStartDelay(long delay){if(delay!=0)throw new IllegalArgumentException("Delayed motion is not supported");}
    @Override public void setInterpolator(TimeInterpolator curve){this.curve=curve==null?new AccelerateDecelerateInterpolator():curve;}
    @Override public TimeInterpolator getInterpolator(){return curve;}
    @Override public boolean isRunning(){return running&&!paused;}
    @Override public boolean isStarted(){return running;}
    @Override public boolean isPaused(){return paused;}
    private void notifyEvent(int event){
        ArrayList<AnimatorListener> listeners=getListeners();if(listeners==null)return;
        // Listener callbacks can remove/restart owners; snapshot once per lifecycle event, never per frame.
        for(AnimatorListener l:new ArrayList<>(listeners)){
            if(event==0)l.onAnimationStart(this);else if(event==1)l.onAnimationCancel(this);else l.onAnimationEnd(this);
        }
    }
    @Override public void addPauseListener(AnimatorPauseListener listener){if(listener==null)return;if(pauseListeners==null)pauseListeners=new ArrayList<>();if(!pauseListeners.contains(listener))pauseListeners.add(listener);}
    @Override public void removePauseListener(AnimatorPauseListener listener){if(pauseListeners!=null)pauseListeners.remove(listener);}
    private void notifyPause(boolean value){if(pauseListeners!=null)for(AnimatorPauseListener l:new ArrayList<>(pauseListeners)){if(value)l.onAnimationPause(this);else l.onAnimationResume(this);}}
    private void render(float value){
        fraction=value;float transformed=curve.getInterpolation(value);
        if(FlexyMotionSettings.profile(owner.getContext())==FlexyMotionProfile.FLOW)transformed=Math.max(0,Math.min(1,transformed));
        property.onValue(from+(to-from)*transformed);
    }
    @Override public void start(){
        main();if(detachedPending)throw new IllegalStateException("Detached animation is completing");if(running)cancel();running=true;paused=false;fraction=0;
        frames=new FlexyFrameMotion(owner,0,this::render);
        frames.setOnSettingsChanged(()->{if(running&&FlexyMotionSettings.state(owner.getContext()).instant())finish(false,true);});
        owner.addOnAttachStateChangeListener(this);
        notifyEvent(0);if(!running)return;
        frames.animateTimedTo(1,duration,()->finish(false,true));
    }
    /** Gesture scrubbing pauses the timeline; resume() continues from this rendered fraction. */
    public void setCurrentFraction(float value){
        main();if(!Float.isFinite(value))throw new IllegalArgumentException("fraction");
        if(!running||detachedPending)throw new IllegalStateException("not started or detached");
        if(!paused)pause();fraction=Math.max(0,Math.min(1,value));if(frames!=null)frames.snapTo(fraction);else render(fraction);
    }
    @Override public void pause(){main();if(!running||paused||detachedPending)return;paused=true;if(frames!=null)frames.cancel();notifyPause(true);}
    @Override public void resume(){
        main();if(!running||!paused||detachedPending)return;paused=false;notifyPause(false);if(!running||paused)return;
        frames.animateTimedTo(1,Math.max(0,Math.round(duration*(1-fraction))),()->finish(false,true));
    }
    private void finish(boolean cancelled,boolean finalValue){
        if(!running)return;if(detachedPending){UI.removeCallbacks(detachedCleanup);detachedPending=false;}running=false;paused=false;owner.removeOnAttachStateChangeListener(this);
        FlexyFrameMotion previous=frames;frames=null;if(previous!=null)previous.dispose();
        if(finalValue){fraction=1;property.onValue(to);}
        if(cancelled)notifyEvent(1);notifyEvent(2);
    }
    @Override public FlexyMotionAnimator clone(){throw new UnsupportedOperationException("A property owner cannot be cloned");}
    @Override public void setTarget(Object target){if(target!=owner)throw new IllegalArgumentException("owner");}
    @Override public void cancel(){main();finish(true,false);}
    @Override public void end(){main();finish(false,true);}
    @Override public void onViewAttachedToWindow(View v){}
    @Override public void onViewDetachedFromWindow(View v){
        if(!running||detachedPending)return;
        // Completion can dismiss a Window/remove Views. Never run it inside Android's detach traversal.
        FlexyFrameMotion previous=frames;frames=null;if(previous!=null)previous.dispose();
        owner.removeOnAttachStateChangeListener(this);detachedPending=true;UI.post(detachedCleanup);
    }
}
