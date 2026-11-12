/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** Frame-time based motion shared by both lists. No Android clock or frame-rate assumptions. */
public final class ScrollEffectMotion {
    private long lastFrame = -1, lastInput = -1;
    private float target, targetDirection;
    private final Axis amount = new Axis(), direction = new Axis();
    private long velocitySampleTime = -1, touchReleaseStart = -1;
    private double pendingDistance, filteredSpeed, sampleBaseSpeed, sampleSeconds, sampleDecay = 1;
    private float touchAmount, touchDirection;
    public static final long TOUCH_RELEASE_NANOS = 96_000_000L;

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
        touchReleaseStart = -1;
        if (lastInput < 0 || now - lastInput > 120_000_000L || velocitySampleTime < 0) {
            velocitySampleTime = now; pendingDistance = filteredSpeed = sampleBaseSpeed = sampleSeconds = 0; sampleDecay = 1;
        } else {
            // Coalesce callbacks with the same timestamp. Recompute the same velocity sample
            // from its original state instead of applying the filter repeatedly to a burst.
            if (now > velocitySampleTime) {
                sampleSeconds = (now - velocitySampleTime) / 1_000_000_000d;
                sampleBaseSpeed = filteredSpeed; sampleDecay = Math.exp(-sampleSeconds / .060);
                pendingDistance = Math.abs(dy) / viewportHeight;
                velocitySampleTime = now;
            } else {
                pendingDistance += Math.abs(dy) / viewportHeight;
            }
            if (sampleSeconds > 0) filteredSpeed = sampleBaseSpeed * sampleDecay
                    + pendingDistance / sampleSeconds * (1 - sampleDecay);
        }
        target = (float) (.30 + .55 * filteredSpeed / (filteredSpeed + .8));
        targetDirection = Math.signum(dy);
        // Start the clock at input, not with an artificial first-frame impulse.
        if (lastFrame < 0) lastFrame = now;
        lastInput = now;
    }

    public boolean advance(long now) {
        if (lastFrame < 0) return false;
        if (now <= lastFrame) return true;
        if (touchReleaseStart >= 0) {
            double progress = Math.min(1, (now - touchReleaseStart) / (double) TOUCH_RELEASE_NANOS);
            // Quintic release: no position jump, rebound or lingering spring after a direct touch.
            double remaining = 1 - progress;
            double envelope = remaining * remaining * remaining * (1 + 3 * progress + 6 * progress * progress);
            amount.value = touchAmount * envelope;
            amount.velocity = -touchAmount * 30 * progress * progress * remaining * remaining
                    / (TOUCH_RELEASE_NANOS / 1_000_000_000d);
            direction.value = touchDirection; direction.velocity = 0;
            lastFrame = now;
            if (progress == 1) { reset(); return false; }
            return true;
        }
        double seconds = Math.max(0, now - lastFrame) / 1_000_000_000d;
        long expiry = lastInput + 80_000_000L;
        // Integrate across the input expiry exactly, even after a dropped frame.
        double attack = Math.max(0, Math.min(now, expiry) - lastFrame) / 1_000_000_000d;
        amount.advance(target, attack, 48);
        double release = seconds - attack;
        amount.advance(0, release, 42);
        direction.advance(targetDirection, seconds, 60);
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
    public void interrupt(long now, float displayedAmount, float displayedDirection) {
        touchAmount = Math.max(0, Math.min(1, displayedAmount));
        touchDirection = Math.max(-1, Math.min(1, displayedDirection));
        amount.value = touchAmount; amount.velocity = 0;
        direction.value = touchDirection; direction.velocity = 0;
        lastFrame = touchReleaseStart = now;
        lastInput = velocitySampleTime = -1; pendingDistance = filteredSpeed = sampleBaseSpeed = sampleSeconds = 0; sampleDecay = 1;
    }
    public void reset() {
        lastFrame = lastInput = velocitySampleTime = touchReleaseStart = -1;
        target = targetDirection = touchAmount = touchDirection = 0;
        pendingDistance = filteredSpeed = sampleBaseSpeed = sampleSeconds = 0; sampleDecay = 1; amount.reset(); direction.reset();
    }
}
