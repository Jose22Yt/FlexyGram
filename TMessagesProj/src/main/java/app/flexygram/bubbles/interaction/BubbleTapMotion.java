/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.os.SystemClock;
import android.view.View;
import app.exteraless.player.Spring;

/** Local frame-clock spring; the existing native integrator owns position AND velocity. */
public final class BubbleTapMotion implements Runnable {
    private final View owner;
    private final Spring x = new Spring(1f, 560f, .72f, .00012f);
    private final Spring y = new Spring(1f, 560f, .72f, .00012f);
    private boolean pressed, running;
    private long last;
    public BubbleTapMotion(View owner) { this.owner = owner; }
    public float scale() { return (x.value + y.value) * .5f; }
    public float scaleX() { return x.value; }
    public float scaleY() { return y.value; }
    public float velocityX() { return x.velocity(); }
    public float velocityY() { return y.velocity(); }
    public boolean pressed() { return pressed; }

    public void press(float compression, float rebound, long duration) {
        // Old arguments are retained for binary/source compatibility only. Physics is fixed.
        pressed = true;
        x.target = .986f;
        y.target = .970f;
        // Integrate the first sub-frame on DOWN; no abrupt scale assignment.
        x.step(1f / 240f); y.step(1f / 240f);
        invalidate();
        schedule();
    }
    public void release() {
        if (!pressed) return;
        pressed = false;
        x.target = y.target = 1f;
        schedule(); // Keeps both current positions and velocities.
    }
    private void schedule() {
        if (running) return;
        running = true; last = SystemClock.uptimeMillis();
        owner.postOnAnimation(this);
    }
    @Override public void run() {
        if (!running) return;
        long now = SystemClock.uptimeMillis();
        float dt = Math.max(0f, Math.min(.064f, (now-last)/1000f)); last = now;
        boolean movingX = x.step(dt), movingY = y.step(dt);
        invalidate();
        running = movingX || movingY;
        if (running) owner.postOnAnimation(this);
    }
    /** Compatibility utility; production movement uses the live spring state above. */
    public static float recovery(float fraction, float rebound) {
        return DampedSpringCurve.progress(Math.max(0f, fraction) * .330f);
    }
    public void reset() {
        if (!pressed && !running && x.value == 1f && y.value == 1f) return;
        owner.removeCallbacks(this); pressed = running = false;
        x.snap(1f); y.snap(1f); invalidate();
    }
    private void invalidate() {
        owner.invalidate();
        if (owner.getParent() instanceof View) ((View) owner.getParent()).invalidate();
    }
}
