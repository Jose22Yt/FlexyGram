/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.deletion;

import android.content.Context;
import android.content.SharedPreferences;

/** Independent visual preference. The Telegram delete operation is never modified. */
public final class DeleteMotionSettings {
    public static final int DEFAULT = 0;
    public static final int CRYSTAL_FRACTURE = 1;
    public static final int LIQUID_FALL = 2;
    public static final int LIQUID_VORTEX = 3;
    public static final int TNT_DISPERSION = 4;
    private static final String FILE = "flexy_delete_motion";
    private static final String KEY = "message_delete_style";

    private DeleteMotionSettings() {}

    public static int sanitize(int value) {
        return value >= DEFAULT && value <= TNT_DISPERSION ? value : DEFAULT;
    }

    public static int get(Context context) {
        return sanitize(context.getApplicationContext()
                .getSharedPreferences(FILE, Context.MODE_PRIVATE).getInt(KEY, DEFAULT));
    }

    public static void set(Context context, int style) {
        SharedPreferences prefs = context.getApplicationContext()
                .getSharedPreferences(FILE, Context.MODE_PRIVATE);
        prefs.edit().putInt(KEY, sanitize(style)).apply();
    }

    public static boolean effectsAllowed() {
        // The native preference and accessibility remain authoritative.
        return org.telegram.messenger.SharedConfig.animationsEnabled()
                && !org.telegram.messenger.AndroidUtilities.isAccessibilityScreenReaderEnabled();
    }

    public static String[] labels() {
        return new String[]{org.telegram.messenger.LocaleController.getString(org.telegram.messenger.R.string.FlexyContextNativeStyle),
                "Crystal Fracture", "Liquid Fall", "Liquid Vortex", "TNT Dispersion"};
    }
}
