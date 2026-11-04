package app.flexygram.bubbles;

import app.exteraless.appearance.GlassContrastPolicy;

/** Per-cell color cache. No sampling, allocations or contrast math on an unchanged scroll frame. */
public final class BubbleTimeContrast {
    private boolean initialized;
    private int original, surface;
    private int ink, halo;

    public void update(int original, int surface) {
        original |= 0xFF000000;
        if (initialized && this.original == original && this.surface == surface) return;
        initialized = true;
        this.original = original;
        this.surface = surface;
        halo = 0;
        if (GlassContrastPolicy.minimumContrast(original, surface) >= 4.5) {
            ink = original;
            return;
        }
        // Transparent fills can straddle both white and black: neither ink is always readable.
        double black = GlassContrastPolicy.minimumContrast(0xFF000000, surface);
        double white = GlassContrastPolicy.minimumContrast(0xFFFFFFFF, surface);
        if (Math.max(black, white) >= 4.5) {
            ink = GlassContrastPolicy.readableInk(original, surface);
        } else {
            ink = GlassContrastPolicy.readableInk(original, surface | 0xFF000000);
            // Protect only the glyph edges. Never draw a panel behind the timestamp.
            halo = GlassContrastPolicy.contrast(ink, 0xFF000000)
                    >= GlassContrastPolicy.contrast(ink, 0xFFFFFFFF) ? 0xFF000000 : 0xFFFFFFFF;
        }
    }

    public int ink() { return ink; }
    public int halo() { return halo; }
}
