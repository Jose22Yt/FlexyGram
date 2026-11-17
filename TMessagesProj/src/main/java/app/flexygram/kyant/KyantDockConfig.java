package app.flexygram.kyant;

import java.util.ArrayList;
import org.telegram.messenger.ApplicationLoader;
import android.content.Context;

/** UI-thread ownership. The optional dock material has no authority over Telegram's other glass. */
public final class KyantDockConfig {
    private static final String KEY = "flexy_kyant_home_dock";
    private static boolean loaded, enabled;
    private static final ArrayList<Runnable> listeners = new ArrayList<>();
    private KyantDockConfig() {}
    public static boolean isEnabled() {
        if (!loaded && ApplicationLoader.applicationContext != null) {
            enabled = ApplicationLoader.applicationContext.getSharedPreferences("mainconfig", Context.MODE_PRIVATE).getBoolean(KEY, false);
            loaded = true;
        }
        return enabled;
    }
    public static void setEnabled(boolean value) {
        if (ApplicationLoader.applicationContext == null || isEnabled() == value) return;
        ApplicationLoader.applicationContext.getSharedPreferences("mainconfig", Context.MODE_PRIVATE).edit().putBoolean(KEY, value).apply();
        enabled = value;
        for (Runnable listener : new ArrayList<>(listeners)) listener.run();
    }
    public static void addListener(Runnable listener) { if (!listeners.contains(listener)) listeners.add(listener); }
    public static void removeListener(Runnable listener) { listeners.remove(listener); }
}
