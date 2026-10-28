/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.graphics.Canvas;
import android.graphics.RectF;
import android.view.View;
import app.flexygram.motion.FlexyFrameMotion;
import app.flexygram.motion.FlexyMotionSettings;

/**
 * Owns only the bubble draw transform, not the RecyclerView cell, touch dispatch or layout.
 * Host calls down()/up()/cancel() after native hit testing, and wraps ONLY bubble paint
 * in saveBubble()/restoreBubble(). Do not scale links, action widgets or the entire cell.
 */
public final class BubbleTapMotion {
    private final View owner;
    private final FlexyFrameMotion scale;
    private float factor = 1f;
    private boolean pressed;
    public BubbleTapMotion(View owner) {
        if (owner == null) throw new IllegalArgumentException("owner");
        this.owner = owner;
        scale = new FlexyFrameMotion(owner, 1f, value -> {
            factor = value;
            owner.invalidate();
        });
    }
    public void down() {
        if (!BubbleInteractionSettings.tapMotion(owner.getContext())) return;
        FlexyMotionSettings.State s = FlexyMotionSettings.state(owner.getContext());
        if (s.instant()) { reset(); return; }
        pressed = true;
        scale.animateTimedTo(Math.max(.94f, Math.min(1f, s.pressedScale)), 65L, null);
    }
    public void up() {
        if (!pressed) return;
        pressed = false;
        FlexyMotionSettings.State s = FlexyMotionSettings.state(owner.getContext());
        if (s.instant()) reset();
        else {
            // A very fast tap may arrive before the first timed press frame.
            // Guarantee a visible small impulse without restarting an in-flight spring.
            if (factor > .995f) scale.snapTo(Math.max(.94f, Math.min(.985f, s.pressedScale)));
            scale.animateTo(1f); // continuous spring from current position/velocity
        }
    }
    public void cancel() {
        pressed = false;
        scale.animateTo(1f);
    }
    public float factor() { return factor; }
    public int saveBubble(Canvas canvas, RectF bounds) {
        int save = canvas.save();
        if (bounds != null && !bounds.isEmpty() && factor != 1f)
            canvas.scale(factor, factor, bounds.centerX(), bounds.centerY());
        return save;
    }
    public static void restoreBubble(Canvas canvas, int save) { canvas.restoreToCount(save); }
    public void reset() { pressed = false; scale.snapTo(1f); }
    /** Must be called on cell destruction/rebinding; never retain recycled MessageObjects. */
    public void dispose() { pressed = false; scale.dispose(); factor = 1f; }
}
