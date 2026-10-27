/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

/**
 * Small allocation-free, frame-rate-independent damped spring integrator.
 * Owns no UI resources. Target changes preserve the current velocity.
 */
public final class FlexyMotionSpring {
    private static final float MAX_STEP_SECONDS = 1f / 120f;
    private static final float MAX_FRAME_SECONDS = 0.048f;
    private float value;
    private float velocity;
    private float target;
    private float stiffness = FlexyMotionProfile.FLOW.stiffness;
    private float dampingRatio = FlexyMotionProfile.FLOW.dampingRatio;

    public FlexyMotionSpring(float initial) {
        if (!Float.isFinite(initial)) throw new IllegalArgumentException("initial");
        value = target = initial;
    }

    public float value() { return value; }
    public float velocity() { return velocity; }
    public float target() { return target; }

    public void configure(FlexyMotionProfile profile) {
        if (profile == null) throw new IllegalArgumentException("profile");
        stiffness = profile.stiffness;
        dampingRatio = profile.dampingRatio;
    }

    public void target(float next) {
        if (!Float.isFinite(next)) throw new IllegalArgumentException("target");
        target = next;
    }

    public void snapTo(float next) {
        target(next);
        value = next;
        velocity = 0f;
    }

    public boolean settled() {
        return Math.abs(value - target) <= 0.0006f && Math.abs(velocity) <= 0.004f;
    }

    /** A delayed or resumed frame never causes an unbounded integration jump. */
    public float advance(float elapsedSeconds) {
        if (!(elapsedSeconds > 0f) || !Float.isFinite(elapsedSeconds) || settled()) {
            if (settled()) snapTo(target);
            return value;
        }
        float dt = Math.min(elapsedSeconds, MAX_FRAME_SECONDS);
        int steps = Math.max(1, (int) Math.ceil(dt / MAX_STEP_SECONDS));
        float h = dt / steps;
        float damping = 2f * dampingRatio * (float) Math.sqrt(stiffness);
        for (int i = 0; i < steps; i++) {
            float acceleration = stiffness * (target - value) - damping * velocity;
            velocity += acceleration * h;
            value += velocity * h;
        }
        if (settled()) snapTo(target);
        return value;
    }
}
