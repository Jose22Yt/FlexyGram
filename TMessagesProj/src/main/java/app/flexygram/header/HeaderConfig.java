package app.flexygram.header;

import android.content.Context;
import android.content.SharedPreferences;
import app.exteraless.appearance.AppearanceConfig;
import org.telegram.messenger.ApplicationLoader;
import java.util.Map;

/** UI-owned snapshot. Legacy choices are read conservatively and never overwritten. */
public final class HeaderConfig {
    private static boolean loaded, signature = true, compact, counter = true;
    private static int opacity = 85;
    private HeaderConfig() { }
    private static SharedPreferences prefs() { return ApplicationLoader.applicationContext.getSharedPreferences("flexygram_header", Context.MODE_PRIVATE); }
    public static void load() {
        Map<String, ?> p = prefs().getAll();
        Map<String, ?> old = AppearanceConfig.getPreferences().getAll();
        Object previous = old.get("OEAppearanceIosChatHeader");
        boolean legacy = Boolean.TRUE.equals(old.get("OEAppearanceIosChatHeaderAuto")) || !(previous instanceof Boolean) || (Boolean) previous;
        Object style = p.get("style"); signature = style instanceof Integer ? (Integer) style == 0 : legacy;
        compact = Boolean.TRUE.equals(p.get("compact")); counter = !Boolean.FALSE.equals(p.get("counter"));
        Object value = p.get("opacity"); opacity = value instanceof Integer ? Math.max(0, Math.min(100, (Integer) value)) : 85;
        loaded = true;
    }
    private static void ensure() { if (!loaded) load(); }
    public static boolean signature() { ensure(); return signature; }
    public static boolean compact() { ensure(); return compact; }
    public static boolean counter() { ensure(); return counter; }
    public static int opacity() { ensure(); return opacity; }
    public static void style(boolean value) { ensure(); signature = value; prefs().edit().putInt("style", value ? 0 : 1).apply(); }
    public static void compact(boolean value) { ensure(); compact = value; prefs().edit().putBoolean("compact", value).apply(); }
    public static void counter(boolean value) { ensure(); counter = value; prefs().edit().putBoolean("counter", value).apply(); }
    public static void opacity(int value) { ensure(); opacity = Math.max(0, Math.min(100, value)); prefs().edit().putInt("opacity", opacity).apply(); }
}
