/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.view.animation.LinearInterpolator;

/**
 * Menu-owned native canvas transform. One damped timeline for squash, overlay
 * and recovery, with initial X/Y handed off from the press on the real cell.
 */
public final class SelectedBubbleMotion {
    private static final long EXIT_DURATION_MS = 210L;
    private ValueAnimator animator;
    private Runnable invalidate;
    private float scaleX = 1f, scaleY = 1f, progress = 1f;

    public float progress() { return progress; }
    public float scale() { return (scaleX + scaleY) * .5f; }
    public float scaleX() { return scaleX; }
    public float scaleY() { return scaleY; }
    public boolean isRunning() { return animator != null; }

    public void enter(Runnable redraw) {
        enter(redraw, .945f, .960f);
    }

    public void enter(Runnable redraw, float startingX, float startingY) {
        stop();
        invalidate = redraw;
        if (animationsDisabled()) {
            scaleX = scaleY = progress = 1f;
            if (invalidate != null) invalidate.run();
            return;
        }
        scaleX = clamp(startingX, .90f, 1.04f);
        scaleY = clamp(startingY, .90f, 1.04f);
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
        final float startX = scaleX, startY = scaleY, startProgress = progress;
        final long duration = closing ? EXIT_DURATION_MS : DampedSpringCurve.DURATION_MS;
        final ValueAnimator running = ValueAnimator.ofFloat(0f, 1f);
        animator = running;
        running.setInterpolator(new LinearInterpolator());
        running.setDuration(duration);
        running.addUpdateListener(frame -> {
            if (animator != running) return;
            float seconds = frame.getAnimatedFraction() * duration / 1000f;
            float spring = DampedSpringCurve.progress(seconds);
            float bounded = clamp(spring, 0f, 1f);
            progress = closing ? startProgress * (1f - bounded) : bounded;
            scaleX = startX + (1f - startX) * spring;
            scaleY = startY + (1f - startY) * spring;
            if (invalidate != null) invalidate.run();
        });
        running.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator ended) {
                if (animator != running) return;
                animator = null;
                scaleX = scaleY = 1f;
                progress = closing ? 0f : 1f;
                Runnable callback = invalidate;
                if (closing) invalidate = null;
                if (callback != null) callback.run();
            }
        });
        running.start();
    }

    private static float clamp(float v, float min, float max) {
        return Math.max(min, Math.min(max, v));
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
        scaleX = scaleY = progress = 1f;
        Runnable callback = invalidate;
        invalidate = null;
        if (callback != null) callback.run();
    }
}
