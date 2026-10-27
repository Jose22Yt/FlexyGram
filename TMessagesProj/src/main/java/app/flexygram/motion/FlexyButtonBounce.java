/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewTreeObserver;

/** Lazy draw-factor bridge for native ButtonBounce. Never changes View transforms or touch handlers. */
public final class FlexyButtonBounce implements View.OnAttachStateChangeListener,
        ViewTreeObserver.OnWindowVisibilityChangeListener {
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private View owner;
    private ViewTreeObserver observer;
    private final Runnable invalidate;
    private FlexyFrameMotion press, pulse;
    private float progress, pulseScale = 1;
    private boolean held, releasePending;
    private final Runnable release = () -> {
        releasePending = false;
        if (owner != null && visible()) animateRelease();
        else reset(false);
    };

    public FlexyButtonBounce(View owner, Runnable invalidate) {
        if (invalidate == null) throw new IllegalArgumentException("invalidate");
        this.invalidate = invalidate;
        setOwner(owner);
    }

    public void setOwner(View next) {
        if (owner == next) return;
        reset(true);
        disposeFrames();
        if (owner != null) owner.removeOnAttachStateChangeListener(this);
        unobserve();
        owner = next;
        if (next != null) {
            next.addOnAttachStateChangeListener(this);
            if (next.isAttachedToWindow()) observe();
        }
    }

    private boolean visible() {
        return owner != null && owner.isAttachedToWindow()
                && owner.getWindowVisibility() == View.VISIBLE && owner.isShown();
    }

    private void prepare() {
        if (press != null || owner == null) return;
        press = new FlexyFrameMotion(owner, 0, value -> {
            progress = visible() ? value : 0;
            invalidate.run();
        });
        pulse = new FlexyFrameMotion(owner, 1, value -> {
            pulseScale = visible() ? value : 1;
            invalidate.run();
        });
        press.setOnSettingsChanged(() -> {
            if (FlexyMotionSettings.state(owner.getContext()).instant()) reset(false);
            else if (held && visible()) press.animateTo(1);
        });
    }

    public void setPressed(boolean value, float pressMultiplier, float releaseMultiplier, long delay) {
        held = value;
        cancelRelease();
        if (owner == null) return;
        prepare();
        if (!visible() || FlexyMotionSettings.state(owner.getContext()).instant()) {
            reset(false);
            return;
        }
        // Keep the native brief press timeline. Release uses continuous shared-clock spring physics.
        press.setSpeedMultiplier(value ? 1 : safeSpeed(releaseMultiplier));
        if (value) press.animateTimedTo(1, Math.max(1, Math.round(60 * safeMultiplier(pressMultiplier))), null);
        else if (delay > 0) {
            FlexyMotionSettings.State state = FlexyMotionSettings.state(owner.getContext());
            releasePending = true;
            UI.postDelayed(release, Math.min(2000, Math.round(delay * state.profile.timelineScale / state.speed)));
        } else animateRelease();
    }

    private static float safeMultiplier(float value) {
        return Float.isFinite(value) ? Math.max(.1f, Math.min(10, value)) : 1;
    }
    private static float safeSpeed(float multiplier) { return 1 / safeMultiplier(multiplier); }
    private void animateRelease() { if (press != null) press.animateTo(0); }

    public void bounce() {
        if (owner == null || !visible()) return;
        prepare();
        FlexyMotionSettings.State state = FlexyMotionSettings.state(owner.getContext());
        if (state.instant()) { reset(false); return; }
        pulse.snapTo(state.pressedScale);
        pulse.animateTo(1);
    }

    public float progress() {
        return owner == null || !visible() || FlexyMotionSettings.state(owner.getContext()).instant() ? 0 : progress;
    }
    public float scale(float diff) {
        if (owner == null || !visible()) return 1;
        FlexyMotionSettings.State state = FlexyMotionSettings.state(owner.getContext());
        if (state.instant()) return 1;
        float amplitude = Float.isFinite(diff) ? Math.max(0, Math.min(diff, 1 - state.pressedScale)) : 0;
        return (1 - amplitude * progress) * pulseScale;
    }

    private void cancelRelease() {
        if (releasePending) { UI.removeCallbacks(release); releasePending = false; }
    }
    private void reset(boolean forgetHold) {
        cancelRelease();
        if (forgetHold) held = false;
        if (press != null) press.snapTo(0);
        if (pulse != null) pulse.snapTo(1);
        progress = 0;
        pulseScale = 1;
    }
    private void disposeFrames() {
        if (press != null) press.dispose();
        if (pulse != null) pulse.dispose();
        press = pulse = null;
    }
    private void observe() {
        unobserve();
        observer = owner.getViewTreeObserver();
        if (observer.isAlive()) observer.addOnWindowVisibilityChangeListener(this);
    }
    private void unobserve() {
        if (observer != null && observer.isAlive()) observer.removeOnWindowVisibilityChangeListener(this);
        observer = null;
    }
    @Override public void onViewAttachedToWindow(View view) { observe(); }
    @Override public void onViewDetachedFromWindow(View view) { reset(true); disposeFrames(); unobserve(); }
    @Override public void onWindowVisibilityChanged(int visibility) { if (visibility != View.VISIBLE) reset(true); }
    public void dispose() { setOwner(null); }
}
