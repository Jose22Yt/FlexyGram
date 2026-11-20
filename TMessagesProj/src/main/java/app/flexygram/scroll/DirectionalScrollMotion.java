/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** One active edge. A reversal hands off only after the previous edge reaches zero. */
public final class DirectionalScrollMotion {
    private static final float RETURN_MS = 275f, HANDOFF_MS = 105f, RESUME_MS = 100f;
    private static final float MIN_INTENSITY = .002f;
    private int edge, pendingEdge;
    private float intensity, from, target, pendingIntensity;
    private long started;
    private float duration, travel, pendingTravel;

    public int edge() { return edge; }
    public float intensity() { return intensity; }
    public boolean needsFrame() { return duration != 0f; }

    public boolean isFullyEngaged(int direction) {
        return edge == direction && intensity == 1f && !needsFrame();
    }

    public void scroll(int next, float distance, float engagementDistance, long now) {
        advance(now);
        if (edge == DirectionalScrollEdge.NONE) {
            edge = next;
            travel = distance;
            intensity = DirectionalScrollEdge.engagement(travel, engagementDistance);
        } else if (next == edge) {
            travel = Math.min(engagementDistance, travel + distance);
            pendingEdge = DirectionalScrollEdge.NONE;
            if (duration != 0f) {
                // Resume from the current deformation, even halfway through a return.
                if (target == 0f) {
                    animateTo(1f, RESUME_MS, now);
                } else {
                    final float engagement = DirectionalScrollEdge.engagement(travel, engagementDistance);
                    if (engagement > target) animateTo(engagement, RESUME_MS, now);
                }
            } else {
                intensity = Math.max(intensity, DirectionalScrollEdge.engagement(travel, engagementDistance));
            }
        } else {
            if (pendingEdge != next) {
                pendingEdge = next;
                pendingTravel = 0f;
                animateTo(0f, HANDOFF_MS, now);
            }
            pendingTravel = Math.min(engagementDistance, pendingTravel + distance);
            pendingIntensity = DirectionalScrollEdge.engagement(pendingTravel, engagementDistance);
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
            if (edge != DirectionalScrollEdge.NONE) {
                travel = pendingTravel;
                animateTo(pendingIntensity, RESUME_MS, now);
            }
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
