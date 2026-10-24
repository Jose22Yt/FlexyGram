package app.flexygram.settings;

import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.BuildConfig;

/** Never migrates storage. Unknown/updated/restored installations retain the upstream fallback. */
public final class FreshInstallSavePath {
    private FreshInstallSavePath() {}

    public static boolean eligible(boolean alpha, boolean emptyPreferences, long firstInstall, long lastUpdate) {
        return alpha && emptyPreferences && firstInstall > 0 && firstInstall == lastUpdate;
    }

    public static void pin(SharedPreferences preferences) {
        if (preferences == null || !BuildConfig.CONNECTED_ALPHA || !preferences.getAll().isEmpty()) return;
        try {
            PackageInfo info = ApplicationLoader.applicationContext.getPackageManager().getPackageInfo(
                    ApplicationLoader.applicationContext.getPackageName(), 0);
            if (eligible(true, true, info.firstInstallTime, info.lastUpdateTime)) {
                preferences.edit().putString("customSavePath", "FlexyGram").apply();
            }
        } catch (Exception ignored) {
            // No reliable evidence of a new installation: keep the existing default untouched.
        }
    }
}
