/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.os.SystemClock;
import android.view.View;

/**
 * Local, native-frame-clock damped press/release with subtle squash/stretch.
 * Reuses the cell and Canvas; no global animator, view-property mutation,
 * allocations inside a frame, or unnecessary invalidation at rest.
 */
public final class BubbleTapMotion implements Runnable {
    private static final long PRESS_MS = 76L;
    private final View owner;
    private float scaleX = 1f, scaleY = 1f, fromX = 1f, fromY = 1f;
    private float compression, rebound;
    private long started, duration;
    private boolean pressed, running;

    public BubbleTapMotion(View owner) { this.owner = owner; }
    public float scale() { return (scaleX + scaleY) * .5f; }
    public float scaleX() { return scaleX; }
    public float scaleY() { return scaleY; }
    public boolean pressed() { return pressed; }

    public void press(float compression, float rebound, long duration) {
        owner.removeCallbacks(this);
        this.compression = Math.max(0f, Math.min(.065f, compression));
        this.rebound = Math.max(0f, Math.min(1f, rebound));
        this.duration = Math.max(180L, Math.min(480L, duration));
        started = SystemClock.uptimeMillis();
        pressed = true;
        running = true;
        // Immediate feedback without a full-compression jump on ACTION_DOWN.
        scaleX = Math.min(scaleX, 1f - this.compression * .20f);
        scaleY = Math.min(scaleY, 1f - this.compression * .16f);
        fromX = scaleX;
        fromY = scaleY;
        invalidate();
        owner.postOnAnimation(this);
    }

    public void release() {
        if (!pressed) return;
        pressed = false;
        fromX = scaleX;
        fromY = scaleY;
        started = SystemClock.uptimeMillis();
        running = true;
        owner.removeCallbacks(this);
        owner.postOnAnimation(this);
    }

    /** Bounded underdamped return with an exact endpoint. */
    public static float recovery(float fraction, float rebound) {
        if (fraction >= 1f) return 1f;
        if (fraction <= 0f) return 0f;
        float attenuation = (float) Math.exp(-7f * fraction);
        float frequency = (1.50f + rebound * 1.5f) * (float) Math.PI;
        return 1f - attenuation * (float) Math.cos(frequency * fraction);
    }

    @Override public void run() {
        if (!running) return;
        float elapsed = Math.max(0, SystemClock.uptimeMillis() - started);
        if (pressed) {
            float t = Math.min(1f, elapsed / PRESS_MS);
            float ease = 1f - (1f - t) * (1f - t);
            scaleX = fromX + (1f - compression * 1.10f - fromX) * ease;
            scaleY = fromY + (1f - compression * .82f - fromY) * ease;
            if (t >= 1f) running = false;
        } else {
            float t = Math.min(1f, elapsed / duration);
            float x = recovery(t, rebound);
            // Different amplitudes yield a visible but restrained squash/stretch.
            float y = recovery(t, Math.min(1f, rebound + .16f));
            scaleX = fromX + (1f - fromX) * x;
            scaleY = fromY + (1f - fromY) * y;
            if (t >= 1f) {
                scaleX = scaleY = 1f;
                running = false;
            }
        }
        invalidate();
        if (running) owner.postOnAnimation(this);
    }

    public void reset() {
        if (!pressed && !running && scaleX == 1f && scaleY == 1f) return;
        owner.removeCallbacks(this);
        pressed = running = false;
        scaleX = scaleY = 1f;
        invalidate();
    }

    private void invalidate() {
        owner.invalidate();
        if (owner.getParent() instanceof View) ((View) owner.getParent()).invalidate();
    }
}
