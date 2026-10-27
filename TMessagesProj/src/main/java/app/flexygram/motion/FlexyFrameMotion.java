/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.os.Looper;
import android.view.Choreographer;
import android.view.View;

/**
 * Lifecycle-bound frame clock for motion owned by FlexyGram.
 *
 * Unlike ValueAnimator/ObjectAnimator, progress is advanced from Choreographer's
 * frameTimeNanos and is not multiplied by the Android animator duration scale.
 * Does not replace window/IME animations controlled by the operating system.
 *
 * Call all APIs from the main thread. The host still owns presentation and
 * gesture cancellation; do not bind two controllers to the same property.
 */
public final class FlexyFrameMotion implements Choreographer.FrameCallback, View.OnAttachStateChangeListener {
    public interface Listener { void onValue(float value); }

    private final View owner;
    private final Listener listener;
    private final FlexyMotionSpring spring;
    private long previousFrameNanos;
    private boolean scheduled;
    private boolean disposed;

    public FlexyFrameMotion(View owner, float initial, Listener listener) {
        if (owner == null || listener == null) throw new IllegalArgumentException("owner/listener");
        checkMainThread();
        this.owner = owner;
        this.listener = listener;
        spring = new FlexyMotionSpring(initial);
        owner.addOnAttachStateChangeListener(this);
    }

    private static void checkMainThread() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("FlexyFrameMotion requires the main thread");
        }
    }

    public float current() { return spring.value(); }
    public boolean isRunning() { return scheduled; }

    public void animateTo(float target) {
        checkMainThread();
        if (disposed) return;
        FlexyMotionProfile profile = FlexyMotionSettings.effectiveProfile(owner.getContext());
        if (profile == FlexyMotionProfile.FLASH || !owner.isAttachedToWindow()) {
            snapTo(target);
            return;
        }
        spring.configure(profile);
        spring.target(target); // Keep existing velocity when direction changes.
        if (spring.settled()) {
            stopFrames();
            listener.onValue(spring.value());
            return;
        }
        if (!scheduled) {
            // First visible feedback is not delayed by a queued animation.
            listener.onValue(spring.advance(1f / 120f));
            if (!spring.settled()) schedule();
        }
    }

    public void snapTo(float value) {
        checkMainThread();
        if (disposed) return;
        stopFrames();
        spring.snapTo(value);
        listener.onValue(value);
    }

    /** Stop scheduling callbacks without restarting or snapping an interrupted gesture. */
    public void cancel() {
        checkMainThread();
        stopFrames();
    }

    public void dispose() {
        checkMainThread();
        if (disposed) return;
        stopFrames();
        disposed = true;
        owner.removeOnAttachStateChangeListener(this);
    }

    private void schedule() {
        scheduled = true;
        previousFrameNanos = 0L;
        Choreographer.getInstance().postFrameCallback(this);
    }

    private void stopFrames() {
        if (scheduled) Choreographer.getInstance().removeFrameCallback(this);
        scheduled = false;
        previousFrameNanos = 0L;
    }

    @Override public void doFrame(long frameTimeNanos) {
        if (!scheduled || disposed) return;
        if (!owner.isAttachedToWindow()) {
            stopFrames();
            return;
        }
        long delta = previousFrameNanos == 0L ? 8_333_333L
                : Math.max(0L, frameTimeNanos - previousFrameNanos);
        previousFrameNanos = frameTimeNanos;
        listener.onValue(spring.advance(delta * 1e-9f));
        if (spring.settled()) {
            stopFrames();
        } else if (scheduled && !disposed) {
            Choreographer.getInstance().postFrameCallback(this);
        }
    }

    @Override public void onViewAttachedToWindow(View view) { }
    @Override public void onViewDetachedFromWindow(View view) {
        // Keep state for a possible reattach, never leave a frame callback alive.
        stopFrames();
    }
}
