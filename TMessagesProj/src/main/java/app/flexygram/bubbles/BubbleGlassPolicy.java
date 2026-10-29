/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles;

/**
 * Cached wallpaper glass applied inside the native bubble path, never over the chat screen.
 * Pure, allocation-free math for each drawable's alpha; the wallpaper kernel stays shared.
 */
public final class BubbleGlassPolicy {
    private BubbleGlassPolicy() {}
    public static int clamp(int percent) { return Math.max(0, Math.min(100, percent)); }
    public static int opacity(int nativeAlpha, int intensity) {
        final int alpha = Math.max(0, Math.min(255, nativeAlpha));
        return (alpha * clamp(intensity) + 50) / 100;
    }
}
