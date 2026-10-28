/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.SharedPreferences;

/** Chat-scoped presentation preferences. No Telegram account/session data stored here. */
public final class BubbleInteractionSettings {
    private static final String FILE = "flexy_bubble_interaction";
    private static final String TAP = "tap_motion", PANEL = "signature_panel", STICKER = "sticker_conversion";
    private BubbleInteractionSettings() {}
    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static boolean tapMotion(Context context) { return prefs(context).getBoolean(TAP, true); }
    public static boolean signaturePanel(Context context) { return prefs(context).getBoolean(PANEL, false); }
    public static boolean stickerConversion(Context context) { return prefs(context).getBoolean(STICKER, false); }
    public static void setTapMotion(Context context, boolean enabled) { prefs(context).edit().putBoolean(TAP, enabled).apply(); }
    public static void setSignaturePanel(Context context, boolean enabled) { prefs(context).edit().putBoolean(PANEL, enabled).apply(); }
    public static void setStickerConversion(Context context, boolean enabled) { prefs(context).edit().putBoolean(STICKER, enabled).apply(); }
}
