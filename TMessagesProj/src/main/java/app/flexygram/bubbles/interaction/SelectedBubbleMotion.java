/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.view.Choreographer;
import app.exteraless.player.Spring;

/** One native frame owner for the selected message, reactions and action-card progress.
 * Closing retargets existing springs: it never restarts a timed interpolation.
 */
public final class SelectedBubbleMotion implements Choreographer.FrameCallback {
    private final Spring x = new Spring(1f, 560f, .72f, .00012f);
    private final Spring y = new Spring(1f, 560f, .72f, .00012f);
    private final Spring phase = new Spring(1f, 640f, .80f, .0008f);
    private Runnable invalidate, completion;
    private boolean running, closing;
    private long lastFrame, started;
    public float progress() { return Math.max(0f, Math.min(1f, phase.value)); }
    public float panelProgress() { return phase.value; }
    public float scale() { return (x.value + y.value) * .5f; }
    public float scaleX() { return x.value; }
    public float scaleY() { return y.value; }
    public float velocityX() { return x.velocity(); }
    public float velocityY() { return y.velocity(); }
    public boolean isRunning() { return running; }
    public boolean hasOwner() { return invalidate != null; }
    public boolean isClosing() { return closing && invalidate != null; }
    public void enter(Runnable redraw) { enter(redraw, 1f, 1f, 0f, 0f); }
    public void enter(Runnable redraw, float sx, float sy) { enter(redraw, sx, sy, 0f, 0f); }
    public void enter(Runnable redraw, float sx, float sy, float vx, float vy) {
        reset();
        invalidate = redraw; closing = false;
        x.setState(sx, vx); y.setState(sy, vy); x.target = y.target = 1f;
        phase.snap(0f); phase.target = 1f;
        if (!BubbleInteractionSettings.motionEnabled()) {
            x.snap(1f); y.snap(1f); phase.snap(1f); redraw.run(); return;
        }
        redraw.run(); schedule();
    }
    public void close() { close(null); }
    public void close(Runnable done) {
        if (closing) return;
        closing = true; completion = done;
        started = android.os.SystemClock.uptimeMillis();
        x.target = y.target = 1f; phase.target = 0f;
        if (invalidate == null || !BubbleInteractionSettings.motionEnabled()) {
            phase.snap(0f); x.snap(1f); y.snap(1f); finish(); return;
        }
        schedule();
    }
    private void schedule() {
        if (running) return;
        running = true; lastFrame = 0; started = android.os.SystemClock.uptimeMillis();
        Choreographer.getInstance().postFrameCallback(this);
    }
    @Override public void doFrame(long frameTimeNanos) {
        if (!running) return;
        float dt = lastFrame == 0 ? 1f/120f : Math.max(0f, Math.min(.064f, (frameTimeNanos-lastFrame)/1_000_000_000f));
        lastFrame = frameTimeNanos;
        boolean mx=x.step(dt), my=y.step(dt), mp=phase.step(dt);
        if (invalidate != null) invalidate.run();
        if ((!mx && !my && !mp) || android.os.SystemClock.uptimeMillis()-started > 800) {
            running = false;
            x.snap(1f); y.snap(1f); phase.snap(closing ? 0f : 1f);
            if (closing) finish(); else if (invalidate != null) invalidate.run();
        } else Choreographer.getInstance().postFrameCallback(this);
    }
    private void finish() {
        Choreographer.getInstance().removeFrameCallback(this); running = false;
        if (invalidate != null) invalidate.run();
        Runnable done=completion; completion=null; invalidate=null;
        if (done != null) done.run();
    }
    public void reset() {
        Choreographer.getInstance().removeFrameCallback(this); running=false;
        x.snap(1f); y.snap(1f); phase.snap(1f);
        Runnable done=completion; completion=null; invalidate=null; closing=false;
        if (done != null) done.run();
    }
}
