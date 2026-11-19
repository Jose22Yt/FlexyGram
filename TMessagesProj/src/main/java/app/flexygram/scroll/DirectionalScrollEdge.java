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

    public static float fold(int edge, float start, float end, float rowTop, float rowBottom, float band) {
        if (edge == NONE || end <= start || rowBottom <= start || rowTop >= end || band <= 0f) return 0f;
        final float distance = edge == TOP ? rowBottom - start : end - rowTop;
        final float t = Math.max(0f, 1f - distance / band);
        return t * t * (3f - 2f * t);
    }

    public static float settle(float elapsed, float duration) {
        final float remaining = Math.max(0f, 1f - elapsed / duration);
        return remaining * remaining;
    }
}
