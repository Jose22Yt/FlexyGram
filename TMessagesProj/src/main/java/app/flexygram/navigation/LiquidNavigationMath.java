/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

/** Allocation-free bounded shape and spring policy shared by live bar and settings preview. */
public final class LiquidNavigationMath {
    private LiquidNavigationMath() {}
    public static float clamp(float v, float lo, float hi) { return Math.max(lo, Math.min(hi, v)); }
    public static float center(float x, float lo, float hi) { return clamp(x, Math.min(lo, hi), Math.max(lo, hi)); }
    public static float stretch(float distancePx, float slotPx, float elasticity) {
        if (slotPx <= 0) return 0f;
        return clamp(Math.abs(distancePx) / slotPx, 0f, 1f) * clamp(elasticity, 0f, 1f) * .19f;
    }
    public static float width(float slotPx, float stretch) {
        return Math.max(0f, slotPx * (1f + clamp(stretch, 0f, .19f)));
    }
    public static float compression(float stretch) { return 1f - clamp(stretch, 0f, .19f) * .3f; }
    public static int clampPercent(int value) { return Math.max(0, Math.min(100, value)); }
    public static int clampTabs(int value) { return Math.max(2, value); }
}
