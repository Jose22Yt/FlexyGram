/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * One application-local preference, never modifies Android's global animator scales.
 * Explicit reduced-motion preference takes priority over the visual profile.
 */
public final class FlexyMotionSettings {
    private static final String FILE = "flexy_motion_engine";
    private static final String PROFILE = "profile";
    private static final String REDUCE_MOTION = "reduce_motion";

    private FlexyMotionSettings() { }

    private static SharedPreferences preferences(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    public static FlexyMotionProfile profile(Context context) {
        return FlexyMotionProfile.parse(preferences(context).getString(PROFILE, FlexyMotionProfile.FLOW.name()));
    }

    public static void setProfile(Context context, FlexyMotionProfile profile) {
        if (profile == null) throw new IllegalArgumentException("profile");
        preferences(context).edit().putString(PROFILE, profile.name()).apply();
    }

    public static boolean reduceMotion(Context context) {
        return preferences(context).getBoolean(REDUCE_MOTION, false);
    }

    public static void setReduceMotion(Context context, boolean enabled) {
        preferences(context).edit().putBoolean(REDUCE_MOTION, enabled).apply();
    }

    public static FlexyMotionProfile effectiveProfile(Context context) {
        return reduceMotion(context) ? FlexyMotionProfile.FLASH : profile(context);
    }
}
