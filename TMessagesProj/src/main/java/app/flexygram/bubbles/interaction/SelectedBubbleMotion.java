/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.view.animation.LinearInterpolator;

/**
 * Menu-owned native canvas transform. One damped timeline drives presentation,
 * overlay progress and its exit. Never mutates a recycled ChatMessageCell view.
 * Fixed physics: no user-adjustable parameters or global animator service.
 */
public final class SelectedBubbleMotion {
    private static final float ENTER_SCALE = .945f;
    private static final long EXIT_DURATION_MS = 260L;
    private ValueAnimator animator;
    private Runnable invalidate;
    private float scale = 1f;
    private float progress = 1f;
    public float progress() { return progress; }
    public float scale() { return scale; }
    public boolean isRunning() { return animator != null; }

    public void enter(Runnable redraw) {
        stop();
        invalidate = redraw;
        if (animationsDisabled()) {
            scale = 1f;
            progress = 1f;
            if (invalidate != null) invalidate.run();
            return;
        }
        // The selected message starts slightly compressed, then settles with
        // physical underdamped overshoot instead of independent keyframes.
        scale = ENTER_SCALE;
        progress = 0f;
        if (invalidate != null) invalidate.run();
        animate(false);
    }

    public void close() {
        stop();
        if (invalidate == null || animationsDisabled()) {
            reset();
            return;
        }
        animate(true);
    }

    private void animate(boolean closing) {
        final float initialScale = scale;
        final float initialProgress = progress;
        final ValueAnimator running = ValueAnimator.ofFloat(0f, 1f);
        animator = running;
        running.setInterpolator(new LinearInterpolator());
        final long duration = closing ? EXIT_DURATION_MS : DampedSpringCurve.DURATION_MS;
        running.setDuration(duration);
        running.addUpdateListener(frame -> {
            if (animator != running) return;
            float fraction = frame.getAnimatedFraction();
            float seconds = fraction * duration / 1000f;
            // A single spring drives both the selected message and its overlay.
            float response = DampedSpringCurve.progress(seconds);
            float clamped = Math.max(0f, Math.min(1f, response));
            progress = closing ? initialProgress * (1f - clamped) : clamped;
            scale = closing
                    ? initialScale + (1f - initialScale) * response
                    : ENTER_SCALE + (1f - ENTER_SCALE) * response;
            if (invalidate != null) invalidate.run();
        });
        running.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator ended) {
                if (animator != running) return;
                animator = null;
                scale = 1f;
                progress = closing ? 0f : 1f;
                Runnable callback = invalidate;
                if (closing) invalidate = null;
                if (callback != null) callback.run();
            }
        });
        running.start();
    }

    private static boolean animationsDisabled() {
        return android.os.Build.VERSION.SDK_INT >= 26 && !ValueAnimator.areAnimatorsEnabled();
    }

    private void stop() {
        ValueAnimator previous = animator;
        animator = null;
        if (previous != null) {
            previous.removeAllUpdateListeners();
            previous.removeAllListeners();
            previous.cancel();
        }
    }

    public void reset() {
        stop();
        scale = 1f;
        progress = 1f;
        Runnable callback = invalidate;
        invalidate = null;
        if (callback != null) callback.run();
    }
}
