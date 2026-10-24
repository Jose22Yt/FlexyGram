package app.flexygram.bubbles;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** UI-thread snapshot: no preference reads or allocations during native bubble drawing. */
public final class BubbleConfig {
    public static final String FILE = "flexygram_bubbles";
    public static final String GLASS = "glass", TRANSPARENCY = "transparency", BORDER = "border", EDGES = "edges";
    private static boolean loaded, glass, border, edges;
    private static int transparency = 35;
    private BubbleConfig() { }
    private static SharedPreferences preferences() {
        return ApplicationLoader.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static void load() {
        SharedPreferences p = preferences();
        glass = p.getBoolean(GLASS, false); border = p.getBoolean(BORDER, false);
        edges = p.getBoolean(EDGES, false); transparency = BubbleStyle.transparency(p.getInt(TRANSPARENCY, 35)); loaded = true;
    }
    public static boolean glass() { return loaded && glass; }
    public static boolean border() { return loaded && border; }
    public static boolean edges() { return loaded && edges; }
    public static int transparency() { return transparency; }
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
