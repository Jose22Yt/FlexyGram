package app.flexygram.animation;

import android.animation.Animator;
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
        if (!hasContinuousClock(animator)) synchronized (timings) { prepare(animator, systemScale(), false); }
        animator.start();
    }
    private static void prepare(Animator animator, float scale, boolean inheritedDuration) {
        Timing state = timing(animator);
        long duration = animator.getDuration();
        if (!inheritedDuration && duration >= 0) animator.setDuration(state.duration(duration, scale));
        animator.setStartDelay(state.delay(animator.getStartDelay(), scale));
        if (animator instanceof AnimatorSet) {
            boolean inherited = inheritedDuration || duration >= 0;
            for (Animator child : ((AnimatorSet) animator).getChildAnimations()) prepare(child, scale, inherited);
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
        // Only decorative settling springs, never fling/scroller physics or a live back gesture.
        if (FastMotionTiming.isEnabled() && animation instanceof SpringAnimation) {
            SpringAnimation spring=(SpringAnimation)animation;
            if (spring.canSkipToEnd()) spring.skipToEnd();
        }
    }
}
