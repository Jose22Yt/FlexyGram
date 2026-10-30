/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Single source of truth for the two supported message-interaction styles.
 * Older granular keys remain readable for compatibility but the Signature
 * animation uses its own native, fixed physics without customization.
 */
public final class BubbleInteractionSettings {
    public static final int STYLE_DEFAULT = 0;
    public static final int STYLE_SIGNATURE = 1;
    private static final String PREFS = "flexy_bubble_interaction";
    private static final String STYLE_KEY = "interaction_style";
    private static volatile int cachedStyle = -1;
    private static volatile Boolean legacyPanel, legacyBounce;
    private BubbleInteractionSettings() {}

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, 0);
    }

    public static int style(Context context) {
        int value = cachedStyle;
        if (value >= 0) return value;
        SharedPreferences p = prefs(context);
        // Honor the user's previous opt-out. Existing enabled users stay Signature.
        value = p.contains(STYLE_KEY)
                ? p.getInt(STYLE_KEY, STYLE_SIGNATURE)
                : (p.getBoolean("tap_panel", true) ? STYLE_SIGNATURE : STYLE_DEFAULT);
        cachedStyle = value == STYLE_DEFAULT ? STYLE_DEFAULT : STYLE_SIGNATURE;
        return cachedStyle;
    }

    public static void setStyle(Context context, int style) {
        int safe = style == STYLE_DEFAULT ? STYLE_DEFAULT : STYLE_SIGNATURE;
        cachedStyle = safe;
        prefs(context).edit().putInt(STYLE_KEY, safe).apply();
    }

    public static boolean signaturePanel(Context context) {
        if (style(context) != STYLE_SIGNATURE) return false;
        Boolean value = legacyPanel;
        if (value == null) legacyPanel = value = prefs(context).getBoolean("signature_panel", false);
        return value;
    }

    public static void setSignaturePanel(Context context, boolean value) {
        legacyPanel = value;
        prefs(context).edit().putBoolean("signature_panel", value).apply();
    }

    public static boolean springBounce(Context context) {
        if (style(context) != STYLE_SIGNATURE) return false;
        Boolean value = legacyBounce;
        if (value == null) legacyBounce = value = prefs(context).getBoolean("spring_bounce", true);
        return value;
    }

    public static void setSpringBounce(Context context, boolean value) {
        legacyBounce = value;
        prefs(context).edit().putBoolean("spring_bounce", value).apply();
    }

    // Used by ChatMessageCell and ChatActivity: both always follow the selected style.
    public static boolean tapAnimation(Context context) { return style(context) == STYLE_SIGNATURE; }
    public static boolean tapPanel(Context context) { return style(context) == STYLE_SIGNATURE; }

    // Backward-compatible legacy methods; no longer exposed as per-user controls.
    public static void tapAnimation(Context context, boolean value) {
        setStyle(context, value ? STYLE_SIGNATURE : STYLE_DEFAULT);
    }
    public static void tapPanel(Context context, boolean value) {
        setStyle(context, value ? STYLE_SIGNATURE : STYLE_DEFAULT);
    }

    // Fixed values passed to the native cell spring. No adjustable sliders.
    public static int compression(Context context) { return 74; }
    public static int rebound(Context context) { return 68; }
    public static int recovery(Context context) { return 50; }

    public static void parameter(Context context, int which, int value) {
        // Kept for callers compiled against earlier Alpha revisions; intentionally no-op.
    }

    public static void resetTap(Context context) {
        setStyle(context, STYLE_SIGNATURE);
    }
}
