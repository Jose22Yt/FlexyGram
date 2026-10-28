/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.os.Handler;
import android.os.Looper;
import android.view.View;
import androidx.dynamicanimation.animation.FloatValueHolder;
import androidx.dynamicanimation.animation.SpringForce;
import org.telegram.messenger.BuildConfig;
import java.util.ArrayList;

/** Navigation's native spring API bridge. Connected Alpha uses the shared clock; legacy stays native.
 * Completion is queued once: native callers initialize transition flags immediately after start().
 */
public final class SpringAnimation implements View.OnAttachStateChangeListener {
    public interface UpdateListener { void onUpdate(SpringAnimation animation,float value,float velocity); }
    public interface EndListener { void onEnd(SpringAnimation animation,boolean cancelled,float value,float velocity); }
    private static final Handler UI=new Handler(Looper.getMainLooper());
    private final View owner;
    private final FloatValueHolder holder;
    private final ArrayList<UpdateListener> updates=new ArrayList<>();
    private final ArrayList<EndListener> ends=new ArrayList<>();
    private SpringForce force;
    private float initialVelocity;
    private boolean timed,renderInitialValue;
    private long duration;
    private android.animation.ValueAnimator legacyTimeline;
    public SpringAnimation setDuration(long millis){main();if(running||millis<0)throw new IllegalArgumentException("duration");timed=true;duration=millis;return this;}
    private FlexyFrameMotion frames;
    private androidx.dynamicanimation.animation.SpringAnimation legacy;
    private boolean running,queued,queuedCancelled;
    private long generation;
    private static final float NAVIGATION_RATE=1.8f;
    private final Runnable complete=()->{boolean cancelled=queuedCancelled;queued=false;queuedCancelled=false;if(legacy!=null&&cancelled){legacy.cancel();if(running)finish(true);}else if(legacyTimeline!=null&&cancelled){legacyTimeline.cancel();if(running)finish(true);}else finish(cancelled);};
    public SpringAnimation(View owner,FloatValueHolder holder){
        if(owner==null||holder==null)throw new IllegalArgumentException("navigation owner");
        this.owner=owner;this.holder=holder;
    }
    private static void main(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("main thread");}
    public SpringAnimation setSpring(SpringForce force){main();if(running)throw new IllegalStateException("running");if(force==null)throw new IllegalArgumentException("spring");this.force=force;return this;}
    public SpringAnimation setStartVelocity(float velocity){main();if(!Float.isFinite(velocity)||running)throw new IllegalArgumentException("velocity");initialVelocity=velocity;return this;}
    public SpringAnimation addUpdateListener(UpdateListener listener){main();if(listener==null)throw new IllegalArgumentException("listener");updates.add(listener);return this;}
    public SpringAnimation addEndListener(EndListener listener){main();if(listener==null)throw new IllegalArgumentException("listener");ends.add(listener);return this;}
    public boolean isRunning(){return running;}
    /** Snapshot only an active analytic trajectory; timed/legacy/queued completion has no transferable velocity. */
    public boolean canContinue(){main();return BuildConfig.CONNECTED_ALPHA&&running&&!queued&&!timed&&frames!=null&&frames.isRunning()&&owner.isAttachedToWindow()&&owner.isShown()&&owner.getWindowVisibility()==View.VISIBLE&&!FlexyMotionSettings.state(owner.getContext()).instant();}
    /** A visible native timed renderer can transfer its current View properties, not spring velocity. */
    public boolean canCaptureTimed() {
        main();
        return BuildConfig.CONNECTED_ALPHA && running && !queued && timed && frames != null && frames.isRunning()
                && owner.isAttachedToWindow() && owner.isShown() && owner.getWindowVisibility() == View.VISIBLE
                && !FlexyMotionSettings.state(owner.getContext()).instant();
    }
    /** Readiness only: final 0..1 property value and stopped updates; caller validates the scene. */
    public boolean canFinalizeRenderedTimed() {
        main();
        return BuildConfig.CONNECTED_ALPHA && running && timed && !queuedCancelled
                && force != null && force.getFinalPosition() == 1f && holder.getValue() == 1f
                && frames != null && !frames.isRunning() && owner.isAttachedToWindow() && owner.isShown()
                && owner.getWindowVisibility() == View.VISIBLE;
    }
    public float continuationValue(){main();if(!canContinue())throw new IllegalStateException("inactive trajectory");return holder.getValue();}
    public float continuationVelocity(){main();if(!canContinue())throw new IllegalStateException("inactive trajectory");return frames.velocity()*NAVIGATION_RATE*FlexyMotionSettings.state(owner.getContext()).speed;}
    /** Opt-in only for a native renderer seeded from a previous trajectory. */
    public SpringAnimation setRenderInitialValue(boolean value){main();if(running)throw new IllegalStateException("running");renderInitialValue=value;return this;}
    private void update(float value){
        holder.setValue(value);
        float velocity=frames==null?0:frames.velocity()*(timed?1:NAVIGATION_RATE)*FlexyMotionSettings.state(owner.getContext()).speed;
        long ticket=generation;int count=updates.size();for(int i=0;i<count&&running&&ticket==generation;i++)updates.get(i).onUpdate(this,value,velocity);
    }
    public void start(){
        main();if(running)return;if(force==null||!Float.isFinite(force.getFinalPosition()))throw new IllegalStateException("final position");
        generation++;running=true;owner.addOnAttachStateChangeListener(this);
        if(!BuildConfig.CONNECTED_ALPHA){
            if(timed){
                legacyTimeline=android.animation.ValueAnimator.ofFloat(holder.getValue(),force.getFinalPosition());
                legacyTimeline.setDuration(duration);legacyTimeline.setInterpolator(new android.view.animation.LinearInterpolator());
                legacyTimeline.addUpdateListener(a->{if(running&&!queued)update((float)a.getAnimatedValue());});
                legacyTimeline.addListener(new android.animation.AnimatorListenerAdapter(){boolean cancelled;public void onAnimationCancel(android.animation.Animator a){cancelled=true;}public void onAnimationEnd(android.animation.Animator a){finish(cancelled);}});
                legacyTimeline.start();return;
            }
            legacy=new androidx.dynamicanimation.animation.SpringAnimation(holder).setSpring(force).setStartVelocity(initialVelocity);
            legacy.addUpdateListener((a,value,velocity)->{int n=updates.size();for(int i=0;i<n&&running&&!queued;i++)updates.get(i).onUpdate(this,value,velocity);});
            legacy.addEndListener((a,cancelled,value,velocity)->finish(cancelled));legacy.start();return;
        }
        frames=new FlexyFrameMotion(owner,holder.getValue(),this::update,.6f,4f);
        frames.setSpeedMultiplier(timed?1:NAVIGATION_RATE);
        frames.setVelocity(initialVelocity/((timed?1:NAVIGATION_RATE)*FlexyMotionSettings.state(owner.getContext()).speed));
        frames.setOnSettingsChanged(()->{if(running&&FlexyMotionSettings.state(owner.getContext()).instant())queue(false);});
        if(FlexyMotionSettings.state(owner.getContext()).instant()||!owner.isAttachedToWindow()||!owner.isShown())queue(false);
        else if(timed) frames.animateTimedTo(force.getFinalPosition(),duration,()->queue(false));
        else {
            if(renderInitialValue){
                long ticket=generation;
                update(holder.getValue());
                // Rendering can synchronously cancel/restart this actor or accept a newer scene.
                if(!running||ticket!=generation||frames==null||queued)return;
            }
            frames.animateTo(force.getFinalPosition(),()->queue(false));
        }
    }
    /** Synchronously complete a visible analytic actor already approved by its native navigation owner. */
    public boolean finishNow(){main();if(!canContinue())return false;finish(false);return true;}
    /** Drain only an already queued, non-cancelled visible analytic completion approved by the host. */
    public boolean canFinishQueued() {
        main();
        return BuildConfig.CONNECTED_ALPHA && running && queued && !queuedCancelled && !timed
                && frames != null && owner.isAttachedToWindow() && owner.isShown()
                && owner.getWindowVisibility() == View.VISIBLE;
    }
    public boolean finishQueuedNow() {
        main();
        if (!canFinishQueued()) return false;
        finish(false);
        return true;
    }
    private void queue(boolean cancelled){
        if(!running)return;if(frames!=null)frames.cancel();
        queuedCancelled|=cancelled;
        if(!queued){queued=true;UI.post(complete);}
    }
    private void finish(boolean cancelled){
        if(!running)return;
        long ticket=generation;
        if(queued){UI.removeCallbacks(complete);queued=false;}
        owner.removeOnAttachStateChangeListener(this);
        if(!cancelled&&BuildConfig.CONNECTED_ALPHA)update(force.getFinalPosition());
        // Update callbacks may cancel/reenter. The newer generation owns subsequent completion.
        if(!running||ticket!=generation)return;
        running=false;
        if(frames!=null){frames.dispose();frames=null;}
        legacy=null;legacyTimeline=null;
        queuedCancelled=false;
        float finalValue=holder.getValue();
        for(EndListener listener:new ArrayList<>(ends))listener.onEnd(this,cancelled,finalValue,0);
    }
    public void cancel(){
        main();if(!running)return;
        if(legacy!=null){legacy.cancel();return;}
        if(legacyTimeline!=null){legacyTimeline.cancel();return;}
        finish(true);
    }
    @Override public void onViewAttachedToWindow(View view){}
    @Override public void onViewDetachedFromWindow(View view){queue(true);}
}
