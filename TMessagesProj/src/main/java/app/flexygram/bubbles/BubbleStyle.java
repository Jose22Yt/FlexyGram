package app.flexygram.bubbles;

/** Pure bounded presentation policy. Native message layout/selection/media are unchanged. */
public final class BubbleStyle {
    private BubbleStyle() { }
    public static int transparency(int percent) { return Math.max(0, Math.min(100, percent)); }
    // Retain a readable theme tint even at 100%; this control never makes message text translucent.
    public static int tintAlpha(int percent) { return Math.round(255 * Math.max(.18f, 1 - transparency(percent) / 100f)); }
    public static int defaultRadius(boolean alpha) { return alpha ? 20 : 17; }
}
