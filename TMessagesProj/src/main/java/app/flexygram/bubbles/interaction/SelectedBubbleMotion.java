/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.view.animation.LinearInterpolator;

/** Menu-owned canvas transform. Never writes scale/translation to a recycled message cell. */
public final class SelectedBubbleMotion {
    private ValueAnimator animator;
    private Runnable invalidate;
    private float scale = 1f;

    public float scale() { return scale; }
    public boolean isRunning() { return animator != null; }

    public void enter(Runnable invalidate) {
        reset();
        if (!ValueAnimator.areAnimatorsEnabled()) return;
        this.invalidate = invalidate;
        scale = .962f;
        invalidate.run();
        animate(false);
    }

    public void close() {
        stop();
        if (invalidate == null || scale == 1f || !ValueAnimator.areAnimatorsEnabled()) {
            reset();
            return;
        }
        animate(true);
    }

    private void animate(boolean closing) {
        final float from = scale;
        final ValueAnimator running = ValueAnimator.ofFloat(0f, 1f);
        animator = running;
        running.setInterpolator(new LinearInterpolator());
        running.setDuration(closing ? 120L : DampedSpringCurve.DURATION_MS);
        running.addUpdateListener(frame -> {
            if (animator != running) return;
            float t = frame.getAnimatedFraction();
            scale = closing ? from + (1f - from) * (1f - (1f-t)*(1f-t))
                    : .962f + .038f * DampedSpringCurve.progress(t * .330f);
            if (invalidate != null) invalidate.run();
        });
        running.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator animation) {
                if (animator != running) return;
                animator = null;
                scale = 1f;
                Runnable callback = invalidate;
                invalidate = null;
                if (callback != null) callback.run();
            }
        });
        running.start();
    }

    private void stop() {
        ValueAnimator running = animator;
        animator = null;
        if (running != null) {
            running.removeAllUpdateListeners();
            running.removeAllListeners();
            running.cancel();
        }
    }

    public void reset() {
        stop();
        scale = 1f;
        Runnable callback = invalidate;
        invalidate = null;
        if (callback != null) callback.run();
    }
}
