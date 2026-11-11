/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.view.Choreographer;
import app.exteraless.player.Spring;

/** One native frame owner for the selected message, reactions and action-card progress.
 * Its frame clock is independent of the Reduce animations preference.
 * Closing retargets existing springs: it never restarts a timed interpolation.
 */
public final class SelectedBubbleMotion implements Choreographer.FrameCallback {
    private final Spring x = new Spring(1f, 640f, .82f, .0002f);
    private final Spring y = new Spring(1f, 640f, .82f, .0002f);
    private final Spring backdrop = new Spring(0f, 1600f, 1f, .003f);
    private boolean backdropAvailable;
    public float backdropProgress() { return backdropAvailable ? Math.max(0f, Math.min(1f, backdrop.value)) : 0f; }
    public void backdropReady() {
        if (invalidate == null || closing) return;
        if (backdropAvailable) return;
        backdropAvailable = true;backdrop.target = 1f;
        if (!BubbleInteractionSettings.motionEnabled()) { backdrop.snap(1f);invalidate.run();return; }
        schedule();
    }
    private final Spring phase = new Spring(1f, 640f, .82f, .0012f);
    private static final long ENTER_LIMIT_MS = 420, CLOSE_LIMIT_MS = 260;
    private Runnable invalidate, completion;
    private boolean running, closing;
    private long lastFrame, started;
    private long generation;
    public float progress() { return Math.max(0f, Math.min(1f, phase.value)); }
    public float panelProgress() { return phase.value; }
    /** Preserve the spring's overshoot for spatial motion; alpha/reveal stay bounded. */
    public float geometryProgress() { return phase.value; }
    /** A tall preview can travel hundreds of pixels: keep its rebound in the gap. */
    public float spatialOffset(float distance, float maxOvershoot) {
        float p = phase.value;
        if (maxOvershoot <= 0f) return distance * p;
        if (p < 0f) return maxOvershoot * (float)Math.tanh(distance * p / maxOvershoot);
        if (p <= 1f) return distance * p;
        return distance + maxOvershoot * (float)Math.tanh(distance * (p - 1f) / maxOvershoot);
    }
    public static final float PANEL_START_SCALE = .32f;
    public static final float OPEN_MESSAGE_SCALE = 1.012f;
    public float panelScale() { return Math.max(PANEL_START_SCALE, Math.min(1.025f,
            PANEL_START_SCALE + (1f - PANEL_START_SCALE) * phase.value)); }
    public float panelOffset() { return 10f * Math.max(-.15f, 1f - phase.value); }
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
        x.setState(sx, vx); y.setState(sy, vy); x.target = y.target = OPEN_MESSAGE_SCALE;
        phase.snap(0f); phase.target = 1f;
        // A late bitmap starts its own fade from zero, rather than appearing at a completed phase.
        backdrop.snap(0f); backdrop.target = 0f;
        if (!BubbleInteractionSettings.motionEnabled()) {
            x.snap(OPEN_MESSAGE_SCALE); y.snap(OPEN_MESSAGE_SCALE); phase.snap(1f); redraw.run(); return;
        }
        redraw.run(); schedule();
    }
    public void close() { close(null); }
    public void close(Runnable done) {
        if (closing) return;
        closing = true; completion = done;
        started = android.os.SystemClock.uptimeMillis();
        x.target = y.target = 1f; phase.target = 0f;backdrop.target = 0f;
        if (invalidate == null || !BubbleInteractionSettings.motionEnabled()) {
            phase.snap(0f); x.snap(1f); y.snap(1f); finish(); return;
        }
        schedule();
    }
    private void schedule() {
        if (running || invalidate == null) return;
        running = true;
        started = android.os.SystemClock.uptimeMillis();
        lastFrame = started * 1_000_000L;
        Choreographer.getInstance().postFrameCallback(this);
    }
    @Override public void doFrame(long frameTimeNanos) {
        if (!running) return;
        long frameGeneration = generation;
        // Input can arrive during the same vsync whose frame timestamp precedes the gesture.
        long timestamp = Math.max(lastFrame, frameTimeNanos);
        float dt = (timestamp-lastFrame)/1_000_000_000f;
        lastFrame = timestamp;
        boolean mx=x.stepExact(dt), my=y.stepExact(dt), mp=phase.stepExact(dt), mb=backdrop.stepExact(dt);
        if ((!mx && !my && !mp && !mb) || closing && phase.value <= 0f
                || android.os.SystemClock.uptimeMillis()-started >= (closing ? CLOSE_LIMIT_MS : ENTER_LIMIT_MS) && (closing || !mb)) {
            running = false;
            x.snap(closing ? 1f : OPEN_MESSAGE_SCALE); y.snap(closing ? 1f : OPEN_MESSAGE_SCALE); phase.snap(closing ? 0f : 1f);backdrop.snap(!closing && backdropAvailable ? 1f : 0f);
            if (closing) finish(); else if (invalidate != null) invalidate.run();
        } else {
            if (invalidate != null) invalidate.run();
            // A redraw may synchronously close/reset this owner or hand off to a new gesture.
            if (running && generation == frameGeneration)
                Choreographer.getInstance().postFrameCallback(this);
        }
    }
    /** A new gesture takes priority over the decorative return, with exactly one cleanup callback. */
    public void finishImmediately() {
        closing = true;
        x.snap(1f); y.snap(1f); phase.snap(0f);
        finish();
    }
    private void finish() {
        generation++;
        Choreographer.getInstance().removeFrameCallback(this); running = false;
        backdrop.snap(0f);backdropAvailable=false;
        Runnable redraw=invalidate, done=completion; completion=null; invalidate=null;
        if (redraw != null) redraw.run();
        if (done != null) done.run();
    }
    public void reset() {
        generation++;
        Choreographer.getInstance().removeFrameCallback(this); running=false;
        x.snap(1f); y.snap(1f); phase.snap(1f);backdrop.snap(0f);backdropAvailable=false;
        Runnable done=completion; completion=null; invalidate=null; closing=false;
        if (done != null) done.run();
    }
}
