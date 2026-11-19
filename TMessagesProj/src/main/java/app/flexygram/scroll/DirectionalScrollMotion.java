/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** One active edge. A reversal hands off only after the previous edge reaches zero. */
public final class DirectionalScrollMotion {
    private static final float RETURN_MS = 230f, HANDOFF_MS = 90f, RESUME_MS = 85f;
    private static final float MIN_INTENSITY = .002f;
    private int edge, pendingEdge;
    private float intensity, from, target, pendingIntensity;
    private long started;
    private float duration;

    public int edge() { return edge; }
    public float intensity() { return intensity; }
    public boolean needsFrame() { return duration != 0f; }

    public void scroll(int next, float distance, float engagementDistance, long now) {
        advance(now);
        if (edge == DirectionalScrollEdge.NONE) {
            edge = next;
            intensity = DirectionalScrollEdge.engagement(distance, engagementDistance);
        } else if (next == edge) {
            pendingEdge = DirectionalScrollEdge.NONE;
            if (duration != 0f) {
                // Resume from the current deformation, even halfway through a return.
                if (target == 0f) animateTo(1f, RESUME_MS, now);
            } else {
                intensity = Math.min(1f, intensity + distance / engagementDistance);
            }
        } else {
            if (pendingEdge != next) {
                pendingEdge = next;
                pendingIntensity = DirectionalScrollEdge.engagement(distance, engagementDistance);
                animateTo(0f, HANDOFF_MS, now);
            } else {
                pendingIntensity = Math.min(1f, pendingIntensity + distance / engagementDistance);
            }
        }
    }

    public void stop(long now) {
        advance(now);
        pendingEdge = DirectionalScrollEdge.NONE;
        if (edge == DirectionalScrollEdge.NONE || duration != 0f && target == 0f) return;
        if (intensity <= MIN_INTENSITY) reset();
        else animateTo(0f, RETURN_MS, now);
    }

    public void advance(long now) {
        if (duration == 0f) return;
        final float elapsed = Math.max(0L, now - started);
        intensity = target + (from - target) * DirectionalScrollEdge.settle(elapsed, duration);
        if (elapsed < duration) return;

        intensity = target;
        duration = 0f;
        if (intensity == 0f) {
            edge = pendingEdge;
            pendingEdge = DirectionalScrollEdge.NONE;
            if (edge != DirectionalScrollEdge.NONE) animateTo(pendingIntensity, RESUME_MS, now);
        }
    }

    private void animateTo(float next, float millis, long now) {
        from = intensity;
        target = next;
        duration = millis;
        started = now;
    }

    public void reset() {
        edge = pendingEdge = DirectionalScrollEdge.NONE;
        intensity = duration = 0f;
    }
}
