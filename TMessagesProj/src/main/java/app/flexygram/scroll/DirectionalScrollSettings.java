/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.content.SharedPreferences;
import tw.nekomimi.nekogram.NekoConfig;

public final class DirectionalScrollSettings {
    public static final int OFF = 0, CURVE = 1, TWIST = 2, COUNTER_CURVE = 3, LENS = 4;
    private static final String KEY = "FlexyDirectionalScrollStyle";
    private static final String LEGACY_KEY = "FlexyDirectionalScrollEdge";
    private static int style = load();

    private DirectionalScrollSettings() {}

    private static int load() {
        final SharedPreferences preferences = NekoConfig.getPreferences();
        final int fallback = preferences.getBoolean(LEGACY_KEY, false) ? CURVE : OFF;
        return sanitize(preferences.getInt(KEY, fallback));
    }

    private static int sanitize(int choice) {
        return choice >= OFF && choice <= LENS ? choice : OFF;
    }

    public static int style() {
        return style;
    }

    public static void setStyle(int choice) {
        final int value = sanitize(choice);
        if (style == value) return;
        style = value;
        NekoConfig.getPreferences().edit().putInt(KEY, value).apply();
    }
}
