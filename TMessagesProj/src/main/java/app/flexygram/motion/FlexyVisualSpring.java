/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.view.View;

/** Cached visual property, advanced by the shared clock rather than by onDraw. */
public final class FlexyVisualSpring {
    private final View owner;
    private final float positionThreshold, velocityThreshold;
    private float value, target;
    private FlexyFrameMotion motion;
    public FlexyVisualSpring(View owner, float initial, float positionThreshold, float velocityThreshold) {
        if (owner == null || !Float.isFinite(initial) || !(positionThreshold > 0) || !(velocityThreshold > 0)
                || !Float.isFinite(positionThreshold) || !Float.isFinite(velocityThreshold)) throw new IllegalArgumentException("visual state");
        this.owner = owner;
        value = target = initial;
        this.positionThreshold = positionThreshold;
        this.velocityThreshold = velocityThreshold;
    }
    public float value() { return value; }
    public void animateTo(float target) {
        if (!Float.isFinite(target)) throw new IllegalArgumentException("target");
        if (this.target == target && value == target) return;
        this.target = target;
        if (motion == null) motion = new FlexyFrameMotion(owner, value, v -> { value = v; owner.invalidate(); }, positionThreshold, velocityThreshold);
        motion.animateTo(target);
    }
    public void snap(float target) {
        if (!Float.isFinite(target)) throw new IllegalArgumentException("target");
        this.target = target;
        if (motion != null) motion.snapTo(target);
        else if (value != target) { value = target; owner.invalidate(); }
    }
    public void finish() { snap(target); }
    public void disposeFrames() {
        finish();
        if (motion != null) { motion.dispose(); motion = null; }
    }
}
