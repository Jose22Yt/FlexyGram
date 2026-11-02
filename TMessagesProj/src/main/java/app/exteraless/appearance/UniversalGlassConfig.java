package app.exteraless.appearance;

import android.content.SharedPreferences;
import tw.nekomimi.nekogram.NekoConfig;

/** Separate keys leave the existing Signature/glare preference contract unchanged. */
public final class UniversalGlassConfig {
    private UniversalGlassConfig() {}
    private static SharedPreferences prefs() { return NekoConfig.getPreferences(); }
    public static boolean enabled() { return prefs().getBoolean("FlexyUniversalGlass", false); }
    public static int opacity() { return prefs().getInt("FlexyUniversalGlassOpacity", 42); }
    public static int edge() { return prefs().getInt("FlexyUniversalGlassEdge", 70); }
    public static int surfaces() { return prefs().getInt("FlexyUniversalGlassSurfaces", 63); }
    public static void setEnabled(boolean value) { prefs().edit().putBoolean("FlexyUniversalGlass", value).apply(); }
    public static void setOpacity(int value) { prefs().edit().putInt("FlexyUniversalGlassOpacity", Math.max(20, Math.min(85, value))).apply(); }
    public static void setEdge(int value) { prefs().edit().putInt("FlexyUniversalGlassEdge", Math.max(0, Math.min(100, value))).apply(); }
    public static void setSurfaces(int value) { prefs().edit().putInt("FlexyUniversalGlassSurfaces", value & 63).apply(); }
}
