package app.exteraless.appearance;

import org.telegram.messenger.LiteMode;
import tw.nekomimi.nekogram.NekoConfig;

/** One persisted master switch; rendering reads memory rather than preferences per frame. */
public final class FlexyGlassConfig {
    private static final String KEY = "FlexyBackdropGlassEnabled";
    private static volatile Boolean enabled;
    private FlexyGlassConfig() {}

    public static boolean enabled() {
        Boolean value = enabled;
        if (value == null) {
            synchronized (FlexyGlassConfig.class) {
                if (enabled == null) enabled = NekoConfig.getPreferences().getBoolean(KEY, true);
                value = enabled;
            }
        }
        return value;
    }

    public static void setEnabled(boolean value) {
        if (enabled() == value) return;
        NekoConfig.getPreferences().edit().putBoolean(KEY, value).apply();
        enabled = value;
        LiteMode.onGlassEffectChanged();
    }
}
