/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.deletion;

/** Pure, deterministic motion functions. No Android frame rate or animator scales involved. */
public final class DeleteMotionMath {
    private DeleteMotionMath() {}
    public static float clamp(float v) { return Math.max(0f, Math.min(1f, v)); }
    public static float smooth(float v) { float x = clamp(v); return x * x * (3f - 2f * x); }
    public static float outCubic(float v) { float x = 1f - clamp(v); return 1f - x*x*x; }
    public static float fade(float v, float begin) { return 1f - smooth((v-begin)/(1f-begin)); }
    public static float hash(int value) {
        int x = value ^ (value >>> 16);
        x *= 0x7feb352d; x ^= x >>> 15;
        x *= 0x846ca68b; x ^= x >>> 16;
        return (x & 0x7fffffff) / (float) Integer.MAX_VALUE;
    }
    /** Optional tiny press before fragment release. Exactly one at start and zero after 12%. */
    public static float preCompression(float t) {
        if (t >= .12f) return 1f;
        return 1f - .021f * (float) Math.sin(Math.PI * clamp(t/.12f));
    }
    /** Normalized outward motion: continuous, begins at rest, ends beyond rest. */
    public static float scatter(float t) {
        float x = smooth((t-.10f)/.90f);
        return x*x*(2f-x);
    }
}
