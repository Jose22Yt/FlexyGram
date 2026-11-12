/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** One process snapshot; no preference access in drawing or scrolling callbacks. */
public final class ScrollEffectsConfig {
    public static final int CHATS = 0, CONVERSATION = 1;
    public static final int NONE = 0, WHEEL = 1, PERSPECTIVE = 2, LATERAL = 3;
    public static final String FILE = "flexygram_scroll_effects";
    private static SharedPreferences preferences;
    private static int chats, conversation, intensity = 1;
    private static final SharedPreferences.OnSharedPreferenceChangeListener listener = (prefs, key) -> reload();
    private ScrollEffectsConfig() { }
    public static void load() {
        if (preferences != null) return;
        preferences = ApplicationLoader.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE);
        preferences.registerOnSharedPreferenceChangeListener(listener);
        reload();
    }
    private static void reload() {
        chats = normalizeStyle(preferences.getInt("chats", NONE));
        conversation = normalizeStyle(preferences.getInt("conversation", NONE));
        intensity = normalizeIntensity(preferences.getInt("intensity", 1));
    }
    public static int normalizeStyle(int value) { return value >= NONE && value <= LATERAL ? value : NONE; }
    public static int normalizeIntensity(int value) { return value >= 0 && value <= 2 ? value : 1; }
    public static int style(int surface) { return surface == CONVERSATION ? conversation : chats; }
    public static int intensityIndex() { return intensity; }
    public static float intensity() { return intensity == 0 ? .7f : intensity == 2 ? 1.3f : 1f; }
    public static void setStyle(int surface, int value) {
        load();
        value = normalizeStyle(value);
        if (surface == CONVERSATION) conversation = value; else chats = value;
        preferences.edit().putInt(surface == CONVERSATION ? "conversation" : "chats", value).apply();
    }
    public static void setIntensity(int value) {
        load(); intensity = normalizeIntensity(value);
        preferences.edit().putInt("intensity", intensity).apply();
    }
}
