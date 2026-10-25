package app.flexygram.bubbles;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** UI-thread snapshot: no preference reads or allocations during native bubble drawing. */
public final class BubbleConfig {
    public static final String FILE = "flexygram_bubbles";
    public static final String GLASS = "glass", TRANSPARENCY = "transparency", BORDER = "border", EDGES = "edges";
    private static boolean loaded, glass, border, edges, cachedBlur;
    private static int transparency = 35, borderTenths = 11, outlineStyle, pearlIntensity = 55;
    private static boolean outlineEnabled = true;
    private BubbleConfig() { }
    private static SharedPreferences preferences() {
        return ApplicationLoader.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static void load() {
        SharedPreferences p = preferences();
        outlineEnabled = p.getBoolean("signature_outline_enabled", true);
        outlineStyle = Math.max(0, Math.min(1, p.getInt("signature_outline_style", 0)));
        pearlIntensity = Math.max(0, Math.min(100, p.getInt("signature_pearl_intensity", 55)));
        cachedBlur = p.getBoolean("signature_cached_blur", false);
        borderTenths = Math.max(5, Math.min(20, p.getInt("signature_border_tenths", 11)));
        glass = p.getBoolean(GLASS, false); border = p.getBoolean(BORDER, false);
        edges = p.getBoolean(EDGES, false); transparency = BubbleStyle.transparency(p.getInt(TRANSPARENCY, 35)); loaded = true;
    }
    public static boolean glass() { return loaded && glass; }
    public static boolean border() { return loaded && border; }
    public static boolean edges() { return loaded && edges; }
    public static boolean backgroundBlur() { return cachedBlur; }
    public static void setBackgroundBlur(boolean value) {
        if (!loaded) load();
        if (cachedBlur == value) return;
        cachedBlur = value;
        preferences().edit().putBoolean("signature_cached_blur", value).apply();
    }
    public static boolean outlineEnabled() { return outlineEnabled; }
    public static int outlineStyle() { return outlineStyle; }
    public static int pearlIntensity() { return pearlIntensity; }
    public static void setOutlineEnabled(boolean value) { if (!loaded) load(); outlineEnabled = value; preferences().edit().putBoolean("signature_outline_enabled", value).apply(); }
    public static void setOutlineStyle(int value) { if (!loaded) load(); outlineStyle = Math.max(0, Math.min(1, value)); preferences().edit().putInt("signature_outline_style", outlineStyle).apply(); }
    public static void setPearlIntensity(int value) { if (!loaded) load(); value = Math.max(0, Math.min(100, value)); if (value == pearlIntensity) return; pearlIntensity = value; preferences().edit().putInt("signature_pearl_intensity", value).apply(); }
    public static int transparency() { return transparency; }
    public static int borderTenths() { return borderTenths; }
    public static float borderDp() { return borderTenths / 10f; }
    public static void setBorderTenths(int value) {
        if (!loaded) load();
        value = Math.max(5, Math.min(20, value));
        if (borderTenths == value) return;
        borderTenths = value;
        preferences().edit().putInt("signature_border_tenths", value).apply();
    }
    public static void setGlass(boolean value) {
        if (!loaded) load(); glass = value; preferences().edit().putBoolean(GLASS, value).apply();
    }
    public static void setBorder(boolean value) {
        if (!loaded) load(); border = value; preferences().edit().putBoolean(BORDER, value).apply();
    }
    public static void setEdges(boolean value) {
        if (!loaded) load(); edges = value; preferences().edit().putBoolean(EDGES, value).apply();
    }
    public static void setTransparency(int value) {
        if (!loaded) load(); value = BubbleStyle.transparency(value);
        if (transparency == value) return;
        transparency = value; preferences().edit().putInt(TRANSPARENCY, value).apply();
    }
}
