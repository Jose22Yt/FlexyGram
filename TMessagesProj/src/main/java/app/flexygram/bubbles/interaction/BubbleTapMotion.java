/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.os.SystemClock;
import android.view.View;
import app.exteraless.player.Spring;

/** Local frame-clock spring, independent of Reduce animations; the existing native integrator owns position AND velocity. */
public final class BubbleTapMotion implements Runnable {
    private final View owner;
    private final Spring x = new Spring(1f, 900f, .78f, .0002f);
    private final Spring y = new Spring(1f, 900f, .78f, .0002f);
    private boolean pressed, running;
    private long last, started;
    public BubbleTapMotion(View owner) { this.owner = owner; }
    public float scale() { return (x.value + y.value) * .5f; }
    public float scaleX() { return x.value; }
    public float scaleY() { return y.value; }
    public float velocityX() { return x.velocity(); }
    public float velocityY() { return y.velocity(); }
    public boolean pressed() { return pressed; }

    public void press(float compression, float rebound, long duration) {
        // Old arguments are retained for binary/source compatibility only. Physics is fixed.
        pressed = true; started = SystemClock.uptimeMillis();
        x.target = .978f;
        y.target = .965f;
        // Integrate the first sub-frame on DOWN; no abrupt scale assignment.
        x.step(1f / 240f); y.step(1f / 240f);
        invalidate();
        schedule();
    }
    public void drag(float dx, float dy, float slop) {
        if (!pressed || slop <= 0f) return;
        // Small resistance inside native touch slop. Retarget, never assign position.
        x.target=.978f+.004f*Math.min(1f,Math.abs(dx)/slop);
        y.target=.965f+.006f*Math.min(1f,Math.abs(dy)/slop);
        schedule();
    }
    public void release() {
        if (!pressed) return;
        pressed = false; started = SystemClock.uptimeMillis();
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
        boolean movingX, movingY;
        if (now-started >= 250) {
            x.snap(x.target); y.snap(y.target); movingX=movingY=false;
        } else { movingX=x.step(dt); movingY=y.step(dt); }
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
        if (owner.getParent() instanceof View) {
            View parent=(View)owner.getParent();
            float extra=Math.max(Math.abs(x.value-1f),Math.abs(y.value-1f));
            int pad=(int)Math.ceil(Math.max(owner.getWidth(),owner.getHeight())*extra)+2;
            int left=(int)Math.floor(owner.getX())-parent.getScrollX(), top=(int)Math.floor(owner.getY())-parent.getScrollY();
            parent.invalidate(left-pad,top-pad,left+owner.getWidth()+pad,top+owner.getHeight()+pad);
        }
    }
}
