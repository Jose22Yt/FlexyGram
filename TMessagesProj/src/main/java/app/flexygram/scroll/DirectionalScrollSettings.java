/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import tw.nekomimi.nekogram.NekoConfig;

public final class DirectionalScrollSettings {
    private static final String KEY = "FlexyDirectionalScrollEdge";
    private static boolean enabled = NekoConfig.getPreferences().getBoolean(KEY, false);

    private DirectionalScrollSettings() {}

    public static boolean enabled() {
        return enabled;
    }

    public static void setEnabled(boolean value) {
        if (enabled == value) return;
        enabled = value;
        NekoConfig.getPreferences().edit().putBoolean(KEY, value).apply();
    }
}
