package app.exteraless.appearance;

import android.content.SharedPreferences;
import app.flexygram.effects.GlassSettings;
import tw.nekomimi.nekogram.NekoConfig;

/** Cached settings for the original material. Canceled preview/zone preferences are ignored. */
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
                            p.getInt("FlexySimpleGlassOpacity", 42), p.getInt("FlexySimpleGlassBlur", 40),
                            p.getInt("FlexySimpleGlassEdge", 70), p.getInt("FlexySimpleGlassWidth", 8),
                            p.getInt("FlexySimpleGlassLook", 0), p.getInt("FlexySimpleGlassMaterialIntensity", 55),
                            p.getInt("FlexySimpleGlassFusion", 0), p.getInt("FlexySimpleGlassFusionIntensity", 60),
                            p.getBoolean("FlexySimpleGlassFusionAdapt", true), p.getInt("FlexySimpleGlassPosition", 5));
                }
                value = cached;
            }
        }
        return value;
    }
    public static boolean enabled() { return snapshot().enabled; }
    public static int opacity() { return snapshot().opacity; }
    public static int edge() { return snapshot().edge; }
    public static float blurRadius(float fallback) {
        return enabled() && FlexyGlassConfig.enabled() ? snapshot().blur : fallback;
    }
    public static void save(GlassSettings value) {
        prefs().edit().putBoolean("FlexyUniversalGlass", value.enabled)
                .putInt("FlexySimpleGlassOpacity", value.opacity).putInt("FlexySimpleGlassBlur", value.blur)
                .putInt("FlexySimpleGlassEdge", value.edge).putInt("FlexySimpleGlassWidth", value.width)
                .putInt("FlexySimpleGlassLook", value.look).putInt("FlexySimpleGlassMaterialIntensity", value.materialIntensity)
                .putInt("FlexySimpleGlassFusion", value.fusion).putInt("FlexySimpleGlassFusionIntensity", value.fusionIntensity)
                .putBoolean("FlexySimpleGlassFusionAdapt", value.fusionAdapt).putInt("FlexySimpleGlassPosition", value.position).apply();
        cached = value;
    }
    public static void setEnabled(boolean value) { save(snapshot().with(0, value ? 1 : 0)); }
    public static void setOpacity(int value) { save(snapshot().with(1, value)); }
    public static void setEdge(int value) { save(snapshot().with(3, value)); }
}
