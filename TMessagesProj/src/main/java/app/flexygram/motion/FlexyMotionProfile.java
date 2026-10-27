/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

/** Presets, not Android's system animation multipliers. */
public enum FlexyMotionProfile {
    FLASH(1f, 0f, 1f),
    FLOW(0.975f, 560f, 0.92f),
    SIGNATURE(0.945f, 390f, 0.68f);

    public final float pressedScale;
    public final float stiffness;
    public final float dampingRatio;

    FlexyMotionProfile(float pressedScale, float stiffness, float dampingRatio) {
        this.pressedScale = pressedScale;
        this.stiffness = stiffness;
        this.dampingRatio = dampingRatio;
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
