package org.telegram.ui.Components.blur3;

/** CPU-only sizing policy for FlexyGram's non-refractive backdrop blur. */
public final class GlassRenderingPolicy {
    private GlassRenderingPolicy() {}

    // Preserve full-resolution input only for the explicit scroll-noise suppression path.
    public static int captureScale(boolean suppressScrollNoise) {
        return suppressScrollNoise ? 1 : 8;
    }

    public static int captureDimension(int pixels, int scale) {
        return Math.max(1, pixels / Math.max(1, scale));
    }

    public static int downsampleDimension(int pixels, int captureScale, int blurScale) {
        return Math.max(1, Math.round((float) pixels * captureScale / Math.max(1, blurScale)));
    }
}
