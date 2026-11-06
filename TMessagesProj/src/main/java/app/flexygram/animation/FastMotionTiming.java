package app.flexygram.animation;

/** Presentation timing only. Never apply to network, playback, recording or gesture distances. */
public final class FastMotionTiming {
    public static final double SCALE = 0.01d;
    private static volatile boolean enabled = false;
    private static volatile java.util.function.DoubleSupplier systemScale = () -> 1d;
    private FastMotionTiming() {}
    public static boolean isEnabled() { return enabled; }
    public static void setEnabled(boolean value) { enabled = value; }
    public static void setSystemScaleProvider(java.util.function.DoubleSupplier provider) { systemScale = provider; }
    public static long duration(long nominal) { return enabled ? scale(nominal, 1f, true) : nativeTiming(nominal, true); }
    public static long delay(long nominal) { return enabled ? scale(nominal, 1f, false) : nativeTiming(nominal, false); }
    // Android applies its own multiplier; never apply it twice when fast motion is off.
    public static long animatorDuration(long nominal, float systemScale) { return enabled ? scale(nominal, systemScale, true) : nominal; }
    public static long animatorDelay(long nominal, float systemScale) { return enabled ? scale(nominal, systemScale, false) : nominal; }
    public static float frameDelta(float elapsedSeconds) {
        if (enabled) return elapsedSeconds;
        double multiplier = nativeMultiplier();
        return multiplier > 0 ? (float)Math.min(.064d, elapsedSeconds / multiplier) : 0f;
    }
    private static double nativeMultiplier() {
        double multiplier = systemScale.getAsDouble();
        return Double.isFinite(multiplier) && multiplier >= 0 ? multiplier : 1d;
    }
    private static long nativeTiming(long nominal, boolean duration) {
        if (nominal <= 0) return nominal;
        double multiplier = nativeMultiplier();
        return Math.max(duration ? 1L : 0L, Math.round(Math.min(Long.MAX_VALUE, nominal * multiplier)));
    }
    private static long scale(long nominal, float systemScale, boolean duration) {
        if (nominal <= 0) return nominal;
        // Android's disabled-animation setting stays disabled. No division by zero/hidden API.
        if (!(systemScale > 0) || !Float.isFinite(systemScale)) systemScale = 1f;
        double result = nominal * (double) SCALE / systemScale;
        return Math.max(duration ? 1L : 0L, Math.round(Math.min(Long.MAX_VALUE, result)));
    }
}
