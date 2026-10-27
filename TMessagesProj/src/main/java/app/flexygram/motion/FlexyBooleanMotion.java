/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.animation.TimeInterpolator;
import android.os.Looper;
import android.view.View;

/** Bounded color/opacity state on the shared timeline. Logical state changes before rendering. */
public final class FlexyBooleanMotion {
    private final View owner;
    private final FlexyFrameMotion.Listener listener;
    private FlexyFrameMotion frames;
    private TimeInterpolator interpolator;
    private long duration;
    private Runnable settingsChanged;
    public void setOnSettingsChanged(Runnable callback) { main(); settingsChanged = callback; }
    private boolean value;
    private float factor, from, distance;

    public FlexyBooleanMotion(View owner, long duration, TimeInterpolator interpolator,
                              FlexyFrameMotion.Listener listener) {
        if (owner == null || listener == null || duration < 0) throw new IllegalArgumentException("state");
        this.owner = owner;
        this.duration = duration;
        this.interpolator = interpolator;
        this.listener = listener;
    }
    public FlexyBooleanMotion(View owner, long duration, TimeInterpolator interpolator,
                              FlexyFrameMotion.Listener listener, boolean initial) {
        this(owner, duration, interpolator, listener);
        value = initial;
        factor = initial ? 1 : 0;
    }
    private static void main() {
        if (Looper.myLooper() != Looper.getMainLooper()) throw new IllegalStateException("main thread");
    }
    public boolean getValue() { return value; }
    public float getFloatValue() { return factor; }
    public void setDuration(long duration) {
        main(); if (duration < 0) throw new IllegalArgumentException("duration"); this.duration = duration;
    }
    public void setInterpolator(TimeInterpolator interpolator) { main(); this.interpolator = interpolator; }
    private void emit(float factor) {
        factor = Math.max(0, Math.min(1, factor));
        if (this.factor != factor) { this.factor = factor; listener.onValue(factor); }
    }
    private void render(float fraction) {
        float curved = interpolator == null ? fraction : interpolator.getInterpolation(fraction);
        emit(from + distance * curved);
    }
    public void setValue(boolean value, boolean animated) {
        main();
        if (this.value == value && animated) return;
        this.value = value;
        if (!animated || duration == 0 || FlexyMotionSettings.state(owner.getContext()).instant()
                || !owner.isAttachedToWindow() || !owner.isShown()) { finish(); return; }
        from = factor;
        distance = (value ? 1 : 0) - from;
        if (distance == 0) { finish(); return; }
        if (frames == null) {
            frames = new FlexyFrameMotion(owner, 0, this::render);
            frames.setOnSettingsChanged(() -> { if (settingsChanged != null) settingsChanged.run(); });
        }
        frames.snapTo(0);
        frames.animateTimedTo(1, duration, this::finish);
    }
    public void finish() {
        main();
        if (frames != null) frames.cancel();
        emit(value ? 1 : 0);
    }
    public void disposeFrames() {
        finish();
        if (frames != null) { frames.dispose(); frames = null; }
    }
}
