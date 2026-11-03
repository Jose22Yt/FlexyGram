/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.branding;

import android.content.SharedPreferences;
import android.content.Context;
import android.content.pm.PackageInfo;
import java.io.File;

/** Public product identity; package/resource/preference IDs remain compatible with installed copies. */
public final class FlexyBranding {
    public static final String NAME = "FlexyGram";
    private FlexyBranding() { }

    public static boolean isLegacyDefaultFolder(String value) {
        return value != null && "exteraless".equalsIgnoreCase(value.trim());
    }

    /** Change the inherited default, never a user's custom location or the files themselves. */
    public static void migrateSaveFolder(SharedPreferences preferences) {
        if (preferences == null) return;
        final String current;
        try { current = preferences.getString("customSavePath", null); }
        catch (ClassCastException invalidLegacyValue) { return; }
        if (isLegacyDefaultFolder(current)) preferences.edit().putString("customSavePath", NAME).apply();
    }

    /** Shared pre-scoped storage must not adopt another client's Telegram folder on a fresh install. */
    public static boolean isUpdatedInstallation(Context context) {
        try {
            PackageInfo info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
            return info.firstInstallTime > 0 && info.lastUpdateTime > info.firstInstallTime;
        } catch (Exception unavailable) { return false; }
    }

    /** Existing app-scoped cache paths stay valid for native DB/document references. */
    public static File cacheDirectory(File parent, String legacyName) {
        return cacheDirectory(parent, legacyName, true);
    }

    public static File cacheDirectory(File parent, String legacyName, boolean allowLegacy) {
        String branded = legacyName.startsWith("Telegram") ? NAME + legacyName.substring("Telegram".length()) : legacyName;
        File current = new File(parent, branded);
        if (current.isDirectory()) return current;
        File legacy = new File(parent, legacyName);
        return allowLegacy && legacy.isDirectory() ? legacy : current;
    }
}
