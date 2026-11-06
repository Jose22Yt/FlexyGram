package app.flexygram.icons;

/** Bounded touch feedback, independent of Android's duration multiplier. */
public final class IconPressCurve {
    private IconPressCurve() {}
    public static long duration(boolean reduced) { return reduced ? 80 : 160; }
    public static float scale(float progress, boolean reduced) {
        float t = Math.max(0, Math.min(1, progress));
        float depth = reduced ? .02f : .06f;
        if (t < .4f) return 1 - depth * (float)(.5 - .5 * Math.cos(Math.PI * t / .4));
        float q = (t - .4f) / .6f;
        return 1 - depth * (1-q) * (1-q) * (1-q);
    }
}
