package app.flexygram.bubbles;

import app.exteraless.appearance.GlassContrastPolicy;

/** Per-cell color cache. No sampling, allocations or contrast math on an unchanged scroll frame. */
public final class BubbleTimeContrast {
    private boolean initialized;
    private int original, surface;
    private int ink, backing;

    public void update(int original, int surface) {
        original |= 0xFF000000;
        if (initialized && this.original == original && this.surface == surface) return;
        initialized = true;
        this.original = original;
        this.surface = surface;
        backing = 0;
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
            backing = surface | 0xFF000000;
            ink = GlassContrastPolicy.readableInk(original, backing);
        }
    }

    public int ink() { return ink; }
    public int backing() { return backing; }
}
