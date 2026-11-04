package app.flexygram.animation;

/** Presentation timing only. Never apply to network, playback, recording or gesture distances. */
public final class FastMotionTiming {
    public static final double SCALE = 0.01d;
    private FastMotionTiming() {}
    public static long duration(long nominal) { return scale(nominal, 1f, true); }
    public static long delay(long nominal) { return scale(nominal, 1f, false); }
    public static long animatorDuration(long nominal, float systemScale) { return scale(nominal, systemScale, true); }
    public static long animatorDelay(long nominal, float systemScale) { return scale(nominal, systemScale, false); }
    private static long scale(long nominal, float systemScale, boolean duration) {
        if (nominal <= 0) return nominal;
        // Android's disabled-animation setting stays disabled. No division by zero/hidden API.
        if (!(systemScale > 0) || !Float.isFinite(systemScale)) systemScale = 1f;
        double result = nominal * (double) SCALE / systemScale;
        return Math.max(duration ? 1L : 0L, Math.round(Math.min(Long.MAX_VALUE, result)));
    }
}
