package app.flexygram.bubbles;

/** Pure bounded presentation policy. Native message layout/selection/media are unchanged. */
public final class BubbleStyle {
    public static boolean signature() { return org.telegram.messenger.BuildConfig.CONNECTED_ALPHA; }
    private BubbleStyle() { }
    public static int transparency(int percent) { return Math.max(0, Math.min(100, percent)); }
    // Only fill alpha changes. Text, media, selection and contour keep their own alpha.
    public static int tintAlpha(int percent) { return Math.round(255 * (1 - transparency(percent) / 100f)); }
    public static int outline(int color, boolean dark) {
        int target = dark ? 255 : 32;
        int r = (color >>> 16) & 255, g = (color >>> 8) & 255, b = color & 255;
        r += (target-r)*28/100; g += (target-g)*28/100; b += (target-b)*28/100;
        return 0xff000000 | (r << 16) | (g << 8) | b;
    }
    public static int defaultRadius(boolean alpha) { return alpha ? 20 : 17; }
}
