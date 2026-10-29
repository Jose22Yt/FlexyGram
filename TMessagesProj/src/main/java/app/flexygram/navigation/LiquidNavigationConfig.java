/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Appearance-specific preferences. Does not alter Telegram fragment or account routing. */
public final class LiquidNavigationConfig {
    private static final String NAME = "flexy_liquid_navigation";
    private static final String ENABLED = "drag_indicator";
    private static final String ELASTICITY = "elasticity";
    private static final String OPACITY = "opacity";
    private LiquidNavigationConfig() {}
    private static SharedPreferences prefs() {
        return ApplicationLoader.applicationContext.getSharedPreferences(NAME, Context.MODE_PRIVATE);
    }
    public static boolean enabled() { return prefs().getBoolean(ENABLED, false); }
    public static void enabled(boolean value) { prefs().edit().putBoolean(ENABLED,value).apply(); }
    public static float elasticity() { return LiquidNavigationMath.clamp(prefs().getInt(ELASTICITY, 65) / 100f, 0f, 1f); }
    public static void elasticity(int value) { prefs().edit().putInt(ELASTICITY, LiquidNavigationMath.clampPercent(value)).apply(); }
    public static int opacity() { return LiquidNavigationMath.clampPercent(prefs().getInt(OPACITY, 55)); }
    public static void opacity(int value) { prefs().edit().putInt(OPACITY, LiquidNavigationMath.clampPercent(value)).apply(); }
}
