package app.flexygram.icons;

/** Bounded touch feedback, independent of Android's duration multiplier. */
public final class IconPressCurve {
    private IconPressCurve() {}
    public static long duration(boolean reduced) { return reduced ? 80 : 160; }
    public static float scale(float progress, boolean reduced) {
        return 1.0f;
    }
}
