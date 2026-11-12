/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** Frame-time based motion shared by both lists. No Android clock or frame-rate assumptions. */
public final class ScrollEffectMotion {
    private long lastFrame = -1, lastInput = -1;
    private float target, targetDirection;
    private final Axis amount = new Axis(), direction = new Axis();

    /** Critical damping with an analytical time step; target changes preserve velocity. */
    private static final class Axis {
        double value, velocity;
        void advance(double target, double seconds, double frequency) {
            if (seconds <= 0) return;
            double displacement = value - target;
            double coefficient = velocity + frequency * displacement;
            double decay = Math.exp(-frequency * seconds);
            value = target + (displacement + coefficient * seconds) * decay;
            velocity = (velocity - frequency * coefficient * seconds) * decay;
        }
        void reset() { value = velocity = 0; }
    }

    public void scroll(float dy, float viewportHeight, long now) {
        if (dy == 0 || viewportHeight <= 0) return;
        advance(now);
        // The first event has no measured duration; do not assume a 60 Hz display.
        float seconds = lastInput < 0 ? 0 : Math.max(.001f, (now - lastInput) / 1_000_000_000f);
        float speed = seconds == 0 ? 0 : Math.abs(dy) / viewportHeight / seconds;
        target = .72f + .28f * Math.min(1f, speed / 2f);
        targetDirection = Math.signum(dy);
        // Start the clock at input, not with an artificial first-frame impulse.
        if (lastFrame < 0) lastFrame = now;
        lastInput = now;
    }

    public boolean advance(long now) {
        if (lastFrame < 0) return false;
        if (now <= lastFrame) return true;
        double seconds = Math.max(0, now - lastFrame) / 1_000_000_000d;
        long expiry = lastInput + 80_000_000L;
        // Integrate across the input expiry exactly, even after a dropped frame.
        double attack = Math.max(0, Math.min(now, expiry) - lastFrame) / 1_000_000_000d;
        amount.advance(target, attack, 56);
        double release = seconds - attack;
        amount.advance(0, release, 42);
        direction.advance(targetDirection, seconds, 48);
        lastFrame = now;
        if (now >= expiry && Math.abs(amount.value) < .001 && Math.abs(amount.velocity) < .02) { reset(); return false; }
        return true;
    }

    public float amount() { return (float) Math.max(0, Math.min(1, amount.value)); }
    public float direction() { return (float) Math.max(-1, Math.min(1, direction.value)); }
    public void stop(long now) {
        advance(now);
        if (lastFrame >= 0) lastInput = now - 80_000_000L;
    }
    public void reset() { lastFrame = lastInput = -1; target = targetDirection = 0; amount.reset(); direction.reset(); }
}
