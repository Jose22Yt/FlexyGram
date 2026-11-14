package app.flexygram.animation;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.AnimatorSet;
import android.animation.TimeAnimator;
import android.animation.ValueAnimator;
import android.os.Build;
import android.provider.Settings;
import android.view.View;
import android.view.ViewPropertyAnimator;
import android.view.animation.Animation;
import android.view.animation.AnimationSet;
import androidx.dynamicanimation.animation.DynamicAnimation;
import androidx.dynamicanimation.animation.SpringAnimation;
import org.telegram.messenger.ApplicationLoader;
import java.util.WeakHashMap;

/** Public Android APIs only. Called by the build-time UI animation call-site visitor. */
public final class FastMotion {
    private static final WeakHashMap<Object, Timing> timings = new WeakHashMap<>();
    private static final class Timing {
        long duration, delay, appliedDuration, appliedDelay;
        boolean hasDuration, hasDelay;
        long duration(long current, float scale) {
            if (!hasDuration || current != appliedDuration) duration = current;
            hasDuration = true;
            return appliedDuration = FastMotionTiming.animatorDuration(duration, scale);
        }
        long delay(long current, float scale) {
            if (!hasDelay || current != appliedDelay) delay = current;
            hasDelay = true;
            return appliedDelay = FastMotionTiming.animatorDelay(delay, scale);
        }
    }
    private static final AnimatorListenerAdapter restoreOnEnd = new AnimatorListenerAdapter() {
        @Override public void onAnimationEnd(Animator animator) {
            // An app listener may have already restarted this same animator.
            if (!animator.isStarted()) synchronized (timings) {
                Timing state = timings.get(animator);
                if (state != null) restore(animator, state);
            }
        }
    };
    /** Restore cached timings immediately, including ViewPropertyAnimator's implicit starts.
     * Never cancel an animation, replace app listeners or change Android's global settings.
     */
    public static void setEnabled(boolean enabled) {
        synchronized (timings) {
            boolean wasEnabled = FastMotionTiming.isEnabled();
            FastMotionTiming.setEnabled(enabled);
            if (wasEnabled && !enabled) {
                for (var entry : timings.entrySet()) restore(entry.getKey(), entry.getValue());
            }
        }
    }
    private static void restore(Object owner, Timing state) {
        if (owner instanceof Animator) {
            Animator animator = (Animator) owner;
            if (state.hasDuration && animator.getDuration() == state.appliedDuration)
                animator.setDuration(state.duration);
            if (state.hasDelay && animator.getStartDelay() == state.appliedDelay)
                animator.setStartDelay(state.delay);
        } else if (owner instanceof ViewPropertyAnimator) {
            ViewPropertyAnimator animator = (ViewPropertyAnimator) owner;
            if (state.hasDuration && animator.getDuration() == state.appliedDuration)
                animator.setDuration(state.duration);
            if (state.hasDelay && animator.getStartDelay() == state.appliedDelay)
                animator.setStartDelay(state.delay);
        } else if (owner instanceof Animation) {
            Animation animation = (Animation) owner;
            if (state.hasDuration && animation.getDuration() == state.appliedDuration)
                animation.setDuration(state.duration);
            if (state.hasDelay && animation.getStartOffset() == state.appliedDelay)
                animation.setStartOffset(state.delay);
        }
        state.appliedDuration = state.duration;
        state.appliedDelay = state.delay;
    }
    private FastMotion() {}
    public static float systemScale() {
        if (Build.VERSION.SDK_INT >= 26) return ValueAnimator.getDurationScale();
        if (ApplicationLoader.applicationContext == null) return 1f;
        try {
            return Settings.Global.getFloat(ApplicationLoader.applicationContext.getContentResolver(),
                    Settings.Global.ANIMATOR_DURATION_SCALE, 1f);
        } catch (RuntimeException unavailable) { return 1f; }
    }
    private static Timing timing(Object owner) { return timings.computeIfAbsent(owner, ignored -> new Timing()); }
    private static boolean hasContinuousClock(Animator animator) {
        if (animator instanceof TimeAnimator) return true;
        if (animator instanceof ValueAnimator && ((ValueAnimator) animator).getRepeatCount() == ValueAnimator.INFINITE) return true;
        if (animator instanceof AnimatorSet) for (Animator child : ((AnimatorSet) animator).getChildAnimations())
            if (hasContinuousClock(child)) return true;
        return false;
    }
    public static void start(Animator animator) {
        if (!hasContinuousClock(animator)) synchronized (timings) { prepare(animator, systemScale(), -1L); }
        animator.start();
    }
    public static void reverse(ValueAnimator animator) {
        if (!hasContinuousClock(animator)) synchronized (timings) { prepare(animator, systemScale(), -1L); }
        animator.reverse();
    }
    public static void reverse(AnimatorSet animator) {
        if (!hasContinuousClock(animator)) synchronized (timings) { prepare(animator, systemScale(), -1L); }
        animator.reverse();
    }
    private static void prepare(Animator animator, float scale, long inheritedDuration) {
        Timing state = timing(animator);
        long duration = animator.getDuration();
        // AnimatorSet applies its duration to children on start. Record that
        // nominal duration for each child too; otherwise cached children retain
        // the parent's shortened value after the set finishes or the option flips.
        if (inheritedDuration >= 0) {
            state.duration = inheritedDuration;
            state.hasDuration = true;
            animator.setDuration(state.appliedDuration = FastMotionTiming.animatorDuration(inheritedDuration, scale));
        } else if (duration >= 0) {
            animator.setDuration(state.duration(duration, scale));
        }
        animator.setStartDelay(state.delay(animator.getStartDelay(), scale));
        // Reused animators may have had removeAllListeners() called by their owner.
        if (animator.getListeners() == null || !animator.getListeners().contains(restoreOnEnd)) {
            animator.addListener(restoreOnEnd);
        }
        if (animator instanceof AnimatorSet) {
            long nominal = state.hasDuration ? state.duration : -1L;
            for (Animator child : ((AnimatorSet) animator).getChildAnimations()) prepare(child, scale, nominal);
        }
    }
    public static ViewPropertyAnimator viewAnimator(ViewPropertyAnimator animator) {
        synchronized (timings) {
            Timing state=timing(animator);float scale=systemScale();
            animator.setDuration(state.duration(animator.getDuration(),scale));
            animator.setStartDelay(state.delay(animator.getStartDelay(),scale));
        }
        return animator;
    }
    public static ViewPropertyAnimator duration(ViewPropertyAnimator animator,long nominal) {
        if (nominal < 0) return animator.setDuration(nominal); // Preserve Android's validation.
        synchronized (timings) {
            Timing state=timing(animator);state.duration=nominal;state.hasDuration=true;
            state.appliedDuration=FastMotionTiming.animatorDuration(nominal,systemScale());
            return animator.setDuration(state.appliedDuration);
        }
    }
    public static ViewPropertyAnimator delay(ViewPropertyAnimator animator,long nominal) {
        if (nominal < 0) return animator.setStartDelay(nominal);
        synchronized (timings) {
            Timing state=timing(animator);state.delay=nominal;state.hasDelay=true;
            state.appliedDelay=FastMotionTiming.animatorDelay(nominal,systemScale());
            return animator.setStartDelay(state.appliedDelay);
        }
    }
    public static void start(ViewPropertyAnimator animator) { viewAnimator(animator).start(); }
    public static void startAnimation(View view, Animation animation) {
        if (animation != null) synchronized(timings) { prepareLegacy(animation, false); }
        view.startAnimation(animation);
    }
    private static void prepareLegacy(Animation animation, boolean inheritedDuration) {
        if (animation.getRepeatCount() == Animation.INFINITE) return;
        Timing state=timing(animation);
        if (!inheritedDuration) animation.setDuration(state.duration(animation.getDuration(),1f));
        animation.setStartOffset(state.delay(animation.getStartOffset(),1f));
        if (animation instanceof AnimationSet) for (Animation child : ((AnimationSet) animation).getAnimations())
            prepareLegacy(child,false);
    }
    public static void startSpring(DynamicAnimation<?> animation) {
        animation.start();
    }
}
