/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles;

/**
 * Signature Matte: a diffuse, low-chroma finish derived from the ACTIVE Telegram
 * bubble color. No fake specular highlights, texture bitmaps, blur passes or shaders.
 * The original native silhouette, tint alpha, media, text and tail stay unchanged.
 *
 * Pure arithmetic is safe in the UI draw path; there are no allocations.
 */
public final class SignatureMatteFinish {
    private SignatureMatteFinish() {}

    public static int clampStrength(int strength) {
        return Math.max(0, Math.min(100, strength));
    }

    public static int color(int nativeColor, int strength) {
        final int clamped = clampStrength(strength);
        if (clamped == 0) return nativeColor;
        int r = (nativeColor >>> 16) & 255;
        int g = (nativeColor >>> 8) & 255;
        int b = nativeColor & 255;
        int luminance = (299 * r + 587 * g + 114 * b + 500) / 1000;
        // 0–34% chroma reduction retains the hue but removes the glossy intensity.
        int mute = (clamped * 34 + 50) / 100;
        r += (luminance - r) * mute / 100;
        g += (luminance - g) * mute / 100;
        b += (luminance - b) * mute / 100;
        return (nativeColor & 0xff000000) | (r << 16) | (g << 8) | b;
    }
}
