/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** Geometry for the edge that incoming rows cross, in screen coordinates. */
public final class DirectionalScrollEdge {
    public static final int NONE = 0, TOP = -1, BOTTOM = 1;

    private DirectionalScrollEdge() {}

    public static int forDelta(int previousEdge, int dy) {
        if (dy == 0) return previousEdge;
        return dy > 0 ? BOTTOM : TOP;
    }

    public static float proximity(float y, float edge, float band) {
        return Math.max(0f, 1f - Math.abs(y - edge) / band);
    }

    // Identity and its slope match the native list at either end of the band.
    // Both rows sharing a boundary therefore use the same projected Y.
    public static float projectY(float y, float edge, float proximity, float strength) {
        return y - (y - edge) * strength * proximity * proximity;
    }

    public static float projectX(float x, float center, float proximity, float strength) {
        final float taper = proximity * proximity * (3f - 2f * proximity);
        return x + (center - x) * (strength * .24f) * taper;
    }

    public static float twist(float proximity, float limit, float strength) {
        return limit * strength * proximity * proximity;
    }

    public static float counterOffset(float proximity, float limit, float strength) {
        // Two opposite lateral lobes. Position drives the S, so recycling cannot change its phase.
        final float t = proximity;
        return limit * strength * (4f * t * (1f - t)) * (2f * t - 1f);
    }

    public static float lensScale(float proximity, float limit, float width, float strength) {
        return 1f + 2f * limit / width * strength * proximity * proximity;
    }

    public static float engagement(float travel, float threshold) {
        final float progress = Math.min(1f, travel / threshold);
        return .45f + .55f * progress * (2f - progress);
    }

    public static float settle(float elapsed, float duration) {
        final float remaining = Math.max(0f, 1f - elapsed / duration);
        return remaining * remaining * (3f - 2f * remaining);
    }
}
