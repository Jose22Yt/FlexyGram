package app.flexygram.animation;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Loaded once at startup; rendering reads the timing policy's volatile flag only. */
public final class FastMotionConfig {
    public static final String FILE = "flexygram_motion", KEY = "fast_motion_enabled";
    private static SharedPreferences preferences;
    private static final SharedPreferences.OnSharedPreferenceChangeListener listener = (prefs, key) -> {
        if (key == null || KEY.equals(key)) FastMotion.setEnabled(prefs.getBoolean(KEY, false));
    };
    private FastMotionConfig() {}
    public static synchronized void load() {
        Context context = ApplicationLoader.applicationContext;
        if (context == null) return;
        SharedPreferences next = context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
        if (next != preferences) {
            if (preferences != null) preferences.unregisterOnSharedPreferenceChangeListener(listener);
            preferences = next;
            preferences.registerOnSharedPreferenceChangeListener(listener);
        }
        FastMotionTiming.setSystemScaleProvider(FastMotion::systemScale);
        FastMotion.setEnabled(preferences.getBoolean(KEY, false));
    }
    public static boolean isEnabled() { load(); return FastMotionTiming.isEnabled(); }
    public static synchronized void setEnabled(boolean value) {
        load();
        FastMotion.setEnabled(value);
        if (preferences != null) preferences.edit().putBoolean(KEY, value).apply();
    }
}
