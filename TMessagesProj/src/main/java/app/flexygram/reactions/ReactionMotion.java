/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.reactions;

/** Per-overlay monotonic clock. No timer, Android dependency, allocation or idle work. */
public final class ReactionMotion {
    public static final float FLY_DURATION_MS=240f, LAND_DURATION_MS=200f;
    private long previous = -1;
    public void reset() { previous = -1; }
    public float tick(long now) {
        if (previous < 0) { previous = now; return 0f; }
        float elapsed = elapsed(previous, now);
        previous = Math.max(previous, now);
        return elapsed;
    }
    public static float elapsed(long previous, long now) {
        return Math.max(0f, Math.min(32f, now - previous));
    }
    public static float advance(float progress, float elapsed, float duration) {
        return Math.max(0f, Math.min(1f, progress + Math.max(0f, elapsed) / duration));
    }
    /** A continuous monotonic curve with zero velocity/acceleration at both ends. */
    public static float ease(float progress) {
        double t = Math.max(0f, Math.min(1f, progress));
        return (float)(t * t * t * (t * (t * 6.0 - 15.0) + 10.0));
    }
    public static float lift(float progress, float amplitude) {
        float t = ease(progress);
        return 4f * t * (1f - t) * amplitude;
    }
}
