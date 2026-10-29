/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/**
 * Local contextual-panel response curve. A damped second-order step response:
 * no fixed bounce keyframes, no global motion service, no object allocations.
 *
 * This is a FlexyGram curve inspired by fluid iOS motion, not a claim to use
 * Apple's proprietary animation implementation.
 */
public final class DampedSpringCurve {
    public static final long DURATION_MS = 330L;
    private static final double DAMPING_RATIO = 0.55d;
    private static final double NATURAL_FREQUENCY = 26.0d;
    private static final double COMPLEMENT = Math.sqrt(1.0d - DAMPING_RATIO * DAMPING_RATIO);
    private static final double DAMPED_FREQUENCY = NATURAL_FREQUENCY * COMPLEMENT;
    private DampedSpringCurve() {}

    public static float progress(float seconds) {
        if (seconds <= 0.0f) return 0.0f;
        if (!Float.isFinite(seconds) || seconds * 1000.0f >= DURATION_MS) return 1.0f;
        final double time = seconds;
        final double attenuation = Math.exp(-DAMPING_RATIO * NATURAL_FREQUENCY * time);
        final double oscillation = Math.cos(DAMPED_FREQUENCY * time)
                + DAMPING_RATIO / COMPLEMENT * Math.sin(DAMPED_FREQUENCY * time);
        return (float) (1.0d - attenuation * oscillation);
    }
}
