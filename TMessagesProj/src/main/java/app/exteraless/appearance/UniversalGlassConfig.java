package app.exteraless.appearance;

import android.content.SharedPreferences;
import app.flexygram.effects.GlassSettings;
import tw.nekomimi.nekogram.NekoConfig;

/** One immutable in-memory snapshot. Rendering never reads SharedPreferences per frame. */
public final class UniversalGlassConfig {
    private UniversalGlassConfig() {}
    private static volatile GlassSettings cached;
    private static SharedPreferences prefs() { return NekoConfig.getPreferences(); }
    public static GlassSettings snapshot() {
        GlassSettings value = cached;
        if (value == null) {
            synchronized (UniversalGlassConfig.class) {
                if (cached == null) {
                    SharedPreferences p = prefs();
                    cached = new GlassSettings(p.getBoolean("FlexyUniversalGlass", false),
                            p.getInt("FlexyUniversalGlassOpacity", 42), p.getInt("FlexyGlassBlurRadius", 24),
                            p.getInt("FlexyUniversalGlassEdge", 70), p.getInt("FlexyGlassBorderWidth", 10),
                            p.getInt("FlexyGlassBorderStyle", 1), p.getInt("FlexyGlassBorderColor", 0),
                            p.getInt("FlexyUniversalGlassSurfaces", GlassSettings.ALL_ZONES));
                }
                value = cached;
            }
        }
        return value;
    }
    public static boolean enabled() { return snapshot().enabled; }
    public static int opacity() { return snapshot().opacity; }
    public static int edge() { return snapshot().edge; }
    public static int surfaces() { return snapshot().zones; }
    public static float blurRadius(float fallback) {
        return enabled() && FlexyGlassConfig.enabled() ? snapshot().blur : fallback;
    }
    public static void save(GlassSettings value) {
        prefs().edit().putBoolean("FlexyUniversalGlass", value.enabled)
                .putInt("FlexyUniversalGlassOpacity", value.opacity)
                .putInt("FlexyUniversalGlassEdge", value.edge)
                .putInt("FlexyGlassBlurRadius", value.blur)
                .putInt("FlexyGlassBorderWidth", value.width)
                .putInt("FlexyGlassBorderStyle", value.style)
                .putInt("FlexyGlassBorderColor", value.color)
                .putInt("FlexyUniversalGlassSurfaces", value.zones).apply();
        cached = value;
    }
    public static void setEnabled(boolean value) { save(snapshot().with(0, value ? 1 : 0)); }
    public static void setOpacity(int value) { save(snapshot().with(1, value)); }
    public static void setEdge(int value) { save(snapshot().with(3, value)); }
    public static void setSurfaces(int value) { save(snapshot().with(7, value)); }
}
