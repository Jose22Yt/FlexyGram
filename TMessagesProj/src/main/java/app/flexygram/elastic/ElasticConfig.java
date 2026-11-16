package app.flexygram.elastic;

import android.animation.ValueAnimator;
import android.content.SharedPreferences;
import android.os.Build;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.LiteMode;
import org.telegram.messenger.SharedConfig;

/** Independent preferences: neither switch writes Telegram's glass or animation flags. */
public final class ElasticConfig {
    private static SharedPreferences preferences;
    private static boolean enabled = true, dock;
    private ElasticConfig() {}
    private static void load() {
        if (preferences == null && ApplicationLoader.applicationContext != null) {
            preferences = ApplicationLoader.applicationContext.getSharedPreferences("flexy_elastic_interaction", 0);
            enabled = preferences.getBoolean("enabled", true);
            dock = preferences.getBoolean("kyant_home_dock", false);
        }
    }
    public static boolean enabled() { load(); return enabled; }
    public static boolean kyantDock() { load(); return dock; }
    public static boolean allowed() {
        return enabled() && SharedConfig.animationsEnabled() && !LiteMode.isPowerSaverApplied()
                && (Build.VERSION.SDK_INT < 26 || ValueAnimator.areAnimatorsEnabled());
    }
    public static void setEnabled(boolean value) {
        load(); enabled = value;
        if (preferences != null) preferences.edit().putBoolean("enabled", value).apply();
        if (!value) ElasticInteraction.cancelAll();
    }
    public static void setKyantDock(boolean value) {
        load(); dock = value;
        if (preferences != null) preferences.edit().putBoolean("kyant_home_dock", value).apply();
    }
}
