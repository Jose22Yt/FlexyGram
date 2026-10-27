package app.flexygram.header;

import android.content.Context;
import android.content.SharedPreferences;
import app.exteraless.appearance.AppearanceConfig;
import org.telegram.messenger.ApplicationLoader;
import java.util.Map;

/** UI-owned snapshot. Legacy choices are read conservatively and never overwritten. */
public final class HeaderConfig {
    private static boolean loaded, signature = true, compact, counter = true;
    private static int opacity = 85, counterMode = 1, currentStyle;
    private HeaderConfig() { }
    private static SharedPreferences prefs() { return ApplicationLoader.applicationContext.getSharedPreferences("flexygram_header", Context.MODE_PRIVATE); }
    public static void load() {
        Map<String, ?> p = prefs().getAll();
        Map<String, ?> old = AppearanceConfig.getPreferences().getAll();
        Object previous = old.get("OEAppearanceIosChatHeader");
        boolean legacy = Boolean.TRUE.equals(old.get("OEAppearanceIosChatHeaderAuto")) || !(previous instanceof Boolean) || (Boolean) previous;
        Object style = p.get("style");
        // Once the deprecated iOS Design master switch is retired, its stale
        // preferences cannot choose the conversation header implicitly.
        // Explicit FlexyGram header choices (0/1/2) remain fully respected.
        currentStyle = style instanceof Integer ? (Integer)style == 2 ? 2 : (Integer)style == 0 ? 0 : 1
                : org.telegram.messenger.BuildConfig.CONNECTED_ALPHA ? 0 : legacy ? 0 : 1;
        signature = currentStyle != 1;
        compact = Boolean.TRUE.equals(p.get("compact")); counter = !Boolean.FALSE.equals(p.get("counter"));
        Object mode = p.get("counter_mode");
        counterMode = mode instanceof Integer ? Math.max(1, Math.min(2, (Integer) mode)) : 1;
        Object value = p.get("opacity"); opacity = value instanceof Integer ? Math.max(0, Math.min(100, (Integer) value)) : 85;
        loaded = true;
    }
    private static void ensure() { if (!loaded) load(); }
    public static boolean signature() { ensure(); return signature; }
    public static int style() { ensure(); return currentStyle; }
    public static boolean fusion() { ensure(); return currentStyle == 2; }
    public static boolean compact() { ensure(); return compact; }
    public static boolean counter() { ensure(); return counter; }
    public static int counterMode() { ensure(); return counter ? counterMode : 0; }
    public static void counterMode(int value) { ensure(); counter = value != 0; if (counter) counterMode = Math.max(1, Math.min(2, value)); prefs().edit().putInt("counter_mode", counterMode).putBoolean("counter", counter).apply(); }
    public static int opacity() { ensure(); return opacity; }
    public static void style(boolean value) { style(value ? 0 : 1); }
    public static void style(int value) { ensure(); currentStyle = Math.max(0, Math.min(2, value)); signature = currentStyle != 1; prefs().edit().putInt("style", currentStyle).apply(); }
    public static void compact(boolean value) { ensure(); compact = value; prefs().edit().putBoolean("compact", value).apply(); }
    public static void counter(boolean value) { counterMode(value ? 1 : 0); }
    public static void opacity(int value) { ensure(); opacity = Math.max(0, Math.min(100, value)); prefs().edit().putInt("opacity", opacity).apply(); }
}
