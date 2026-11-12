/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** Frame-time based motion shared by both lists. No Android clock or frame-rate assumptions. */
public final class ScrollEffectMotion {
    private long lastFrame = -1, lastInput = -1;
    private float target, amount, direction, targetDirection;

    public void scroll(float dy, float viewportHeight, long now) {
        if (dy == 0 || viewportHeight <= 0) return;
        advance(now);
        float seconds = lastInput < 0 ? 1f / 60f : Math.max(.001f, (now - lastInput) / 1_000_000_000f);
        float speed = Math.abs(dy) / viewportHeight / seconds;
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
        if (attack > 0) amount = approach(amount, target, attack, .045);
        double release = seconds - attack;
        if (release > 0) amount = approach(amount, 0, release, .070);
        direction = approach(direction, targetDirection, seconds, .055);
        lastFrame = now;
        if (now >= expiry && amount < .001f) { reset(); return false; }
        return true;
    }

    private static float approach(float value, float target, double seconds, double response) {
        return (float) (target + (value - target) * Math.exp(-seconds / response));
    }
    public float amount() { return amount; }
    public float direction() { return direction; }
    public void stop(long now) {
        advance(now);
        if (lastFrame >= 0) lastInput = now - 80_000_000L;
    }
    public void reset() { lastFrame = lastInput = -1; target = amount = direction = targetDirection = 0; }
}
