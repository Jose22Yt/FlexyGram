/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.content.Context;
import android.content.SharedPreferences;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import org.telegram.messenger.ApplicationLoader;

/** UI-owned settings snapshot. Geometry never reads preferences or a clock. */
public final class ScrollEffectsConfig {
    public static final int CHATS = 0, CONVERSATION = 1;
    public static final int NONE = 0, WHEEL = 1;
    public static final String FILE = "flexygram_scroll_effects";
    private static SharedPreferences preferences;
    private static int chats, conversation, curvature = 60;
    private static final ArrayList<WeakReference<Runnable>> listeners = new ArrayList<>();
    private static final SharedPreferences.OnSharedPreferenceChangeListener preferenceListener = (prefs, key) -> {
        reload(); notifyChanged();
    };
    private ScrollEffectsConfig() { }
    public static void load() {
        if (preferences != null) return;
        preferences = ApplicationLoader.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE);
        preferences.registerOnSharedPreferenceChangeListener(preferenceListener);
        reload();
    }
    private static void reload() {
        chats = normalizeStyle(preferences.getInt("chats", NONE));
        conversation = normalizeStyle(preferences.getInt("conversation", NONE));
        int legacy = preferences.getInt("intensity", 1);
        int fallback = legacy == 0 ? 35 : legacy == 2 ? 80 : 60;
        curvature = normalizeCurvature(preferences.getInt("curvature", fallback));
    }
    /** Previously selected perspective/lateral remain enabled, using the sole remaining 3D effect. */
    public static int normalizeStyle(int value) { return value >= 1 && value <= 3 ? WHEEL : NONE; }
    public static int normalizeCurvature(int value) { return Math.max(0, Math.min(100, value)); }
    public static int style(int surface) { return surface == CONVERSATION ? conversation : chats; }
    public static int curvature() { return curvature; }
    public static void observe(Runnable listener) {
        for (int i = listeners.size() - 1; i >= 0; i--) {
            Runnable old = listeners.get(i).get();
            if (old == listener) return;
            if (old == null) listeners.remove(i);
        }
        listeners.add(new WeakReference<>(listener));
    }
    private static void notifyChanged() {
        for (int i = listeners.size() - 1; i >= 0; i--) {
            Runnable listener = listeners.get(i).get();
            if (listener == null) listeners.remove(i); else listener.run();
        }
    }
    public static void setStyle(int surface, int value) {
        load(); value = normalizeStyle(value);
        if (surface == CONVERSATION) conversation = value; else chats = value;
        preferences.edit().putInt(surface == CONVERSATION ? "conversation" : "chats", value).apply();
    }
    /** During a slider gesture update geometry immediately, without a disk write per step. */
    public static void previewCurvature(int value) {
        load(); value = normalizeCurvature(value);
        if (curvature == value) return;
        curvature = value; notifyChanged();
    }
    public static void setCurvature(int value) {
        load(); previewCurvature(value);
        preferences.edit().putInt("curvature", curvature).apply();
    }
}
