/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.content.SharedPreferences;
import tw.nekomimi.nekogram.NekoConfig;

public final class DirectionalScrollSettings {
    private static final String KEY = "FlexyDirectionalScrollStyle";
    private static final String LEGACY_KEY = "FlexyDirectionalScrollEdge";
    private static boolean enabled = load();

    private DirectionalScrollSettings() {}

    private static boolean load() {
        final SharedPreferences preferences = NekoConfig.getPreferences();
        final int style = preferences.getInt(KEY, preferences.getBoolean(LEGACY_KEY, false) ? 1 : 0);
        // Previously enabled styles now use the remaining Curvature renderer.
        return style >= 1 && style <= 4;
    }

    public static boolean enabled() {
        return enabled;
    }

    public static void setEnabled(boolean value) {
        if (enabled == value) return;
        enabled = value;
        NekoConfig.getPreferences().edit().putInt(KEY, value ? 1 : 0).apply();
    }
}
