/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

/** Presets, not Android's system animation multipliers. */
public enum FlexyMotionProfile {
    FLASH(1f, 0f, 1f, 0f),
    FLOW(0.975f, 560f, 0.92f, .8f),
    SIGNATURE(0.945f, 390f, 0.68f, 1f);

    public final float pressedScale;
    public final float stiffness;
    public final float dampingRatio;
    public final float timelineScale;

    FlexyMotionProfile(float pressedScale, float stiffness, float dampingRatio, float timelineScale) {
        this.pressedScale = pressedScale;
        this.stiffness = stiffness;
        this.dampingRatio = dampingRatio;
        this.timelineScale = timelineScale;
    }

    public static FlexyMotionProfile parse(String value) {
        if (value != null) {
            for (FlexyMotionProfile profile : values()) {
                if (profile.name().equalsIgnoreCase(value)) return profile;
            }
        }
        return FLOW;
    }
}
