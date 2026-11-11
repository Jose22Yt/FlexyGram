package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

public class SharedPrefsHelper {
    private static final String WEB_VIEW_SHOWN_DIALOG_FORMAT = "confirm_shown_%d_%d";

    private static volatile SharedPreferences webViewBotsPrefs;

    public static synchronized void init(Context ctx) {
        webViewBotsPrefs = ctx.getSharedPreferences("webview_bots", Context.MODE_PRIVATE);
    }

    private static SharedPreferences prefs() {
        SharedPreferences current = webViewBotsPrefs;
        if (current != null) return current;
        synchronized (SharedPrefsHelper.class) {
            if (webViewBotsPrefs == null) init(ApplicationLoader.applicationContext);
            return webViewBotsPrefs;
        }
    }

    public static boolean isWebViewConfirmShown(int currentAccount, long botId) {
        return prefs().getBoolean(String.format(WEB_VIEW_SHOWN_DIALOG_FORMAT, currentAccount, botId), false);
    }

    public static void setWebViewConfirmShown(int currentAccount, long botId, boolean shown) {
        prefs().edit().putBoolean(String.format(WEB_VIEW_SHOWN_DIALOG_FORMAT, currentAccount, botId), shown).apply();
    }

    public static void cleanupAccount(int account) {
        // A cold logout must also remove records left by a previous process.
        SharedPreferences current = prefs();
        SharedPreferences.Editor editor = current.edit();
        for (String key : current.getAll().keySet()) {
            if (key.startsWith("confirm_shown_" + account + "_")) editor.remove(key);
        }
        editor.apply();
    }

    public static SharedPreferences getWebViewBotsPrefs() {
        return prefs();
    }
}
