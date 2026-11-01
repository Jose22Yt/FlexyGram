/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

public final class LiquidNavigationConfig {
    private static boolean loaded = false;
    private static boolean enabled = true;
    private static boolean showTitles = true;
    private static boolean doubleTapChats = true;
    private static boolean doubleTapProfile = true;
    private static boolean alwaysSearchChats = false;
    private static boolean floatingDock = true;
    private static int[] activeOrder = null;
    // Main tabs remains mounted beneath the settings fragment: notify it immediately.
    private static final java.util.concurrent.CopyOnWriteArrayList<Runnable> changeListeners = new java.util.concurrent.CopyOnWriteArrayList<>();
    public static void addChangeListener(Runnable listener) { if (listener != null) changeListeners.addIfAbsent(listener); }
    public static void removeChangeListener(Runnable listener) { changeListeners.remove(listener); }
    private static void notifyChanged() { for (Runnable listener : changeListeners) listener.run(); }

    private LiquidNavigationConfig() {}

    private static SharedPreferences preferences;
    private static SharedPreferences prefs() {
        if (preferences == null && ApplicationLoader.applicationContext != null) {
            preferences = ApplicationLoader.applicationContext.getSharedPreferences("flexy_bottom_tabs", Context.MODE_PRIVATE);
        }
        return preferences;
    }

    public static void load() {
        if (ApplicationLoader.applicationContext == null) return;
        SharedPreferences p = prefs();
        if (!p.getBoolean("home_defaults_v2", false)) {
            SharedPreferences.Editor edit = p.edit();
            String[] retired = {"height", "compact", "width", "icon", "label_gap", "inner_margin",
                    "bottom_gap", "side_gap", "radius", "speed", "damping", "labels", "bottom_animation",
                    "bottom_compaction", "compaction", "destinations", "enabled", "opacity", "intensity"};
            for (String key : retired) edit.remove(key);
            edit.putBoolean("home_defaults_v2", true).apply();
        }
        enabled = p.getBoolean("show_tabs", true);
        showTitles = p.getBoolean("show_titles", true);
        doubleTapChats = p.getBoolean("double_tap_chats", true);
        doubleTapProfile = p.getBoolean("double_tap_profile", true);
        alwaysSearchChats = p.getBoolean("always_search_chats", false);
        floatingDock = p.getBoolean("floating_dock", true);

        String orderStr = prefs().getString("tab_order", null);
        if (orderStr != null && !orderStr.isEmpty()) {
            String[] parts = orderStr.split(",");
            int[] order = new int[parts.length];
            for (int i = 0; i < parts.length; i++) {
                try {
                    order[i] = Integer.parseInt(parts[i].trim());
                } catch (Exception e) {
                    order[i] = LiquidNavigationDestinations.CHATS;
                }
            }
            activeOrder = LiquidNavigationDestinations.sanitize(order);
        } else {
            activeOrder = LiquidNavigationDestinations.defaults();
        }
        loaded = true;
    }

    private static void ensure() {
        if (!loaded) load();
    }

    public static boolean configured() {
        ensure();
        return enabled;
    }

    public static boolean isEnabled() {
        ensure();
        return enabled;
    }

    public static void setEnabled(boolean value) {
        ensure();
        enabled = value;
        prefs().edit().putBoolean("show_tabs", value).apply();
        notifyChanged();
    }

    public static boolean showTitles() {
        ensure();
        return showTitles;
    }

    public static void setShowTitles(boolean value) {
        ensure();
        showTitles = value;
        prefs().edit().putBoolean("show_titles", value).apply();
        notifyChanged();
    }

    public static boolean doubleTapChats() {
        ensure();
        return doubleTapChats;
    }

    public static void setDoubleTapChats(boolean value) {
        ensure();
        doubleTapChats = value;
        prefs().edit().putBoolean("double_tap_chats", value).apply();
    }

    public static boolean doubleTapProfile() {
        ensure();
        return doubleTapProfile;
    }

    public static void setDoubleTapProfile(boolean value) {
        ensure();
        doubleTapProfile = value;
        prefs().edit().putBoolean("double_tap_profile", value).apply();
    }

    public static boolean alwaysSearchChats() {
        ensure();
        return alwaysSearchChats;
    }

    public static void setAlwaysSearchChats(boolean value) {
        ensure();
        alwaysSearchChats = value;
        prefs().edit().putBoolean("always_search_chats", value).apply();
    }

    public static boolean isFloatingDock() {
        ensure();
        return floatingDock;
    }

    public static void setFloatingDock(boolean value) {
        ensure();
        floatingDock = value;
        prefs().edit().putBoolean("floating_dock", value).apply();
        notifyChanged();
    }

    public static int[] order() {
        ensure();
        if (activeOrder == null) return LiquidNavigationDestinations.defaults();
        return activeOrder;
    }

    public static void setOrder(int[] order) {
        ensure();
        activeOrder = LiquidNavigationDestinations.sanitize(order);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < activeOrder.length; i++) {
            if (i > 0) sb.append(",");
            sb.append(activeOrder[i]);
        }
        prefs().edit().putString("tab_order", sb.toString()).apply();
        notifyChanged();
    }

    public static int[] shown(int slots) {
        return LiquidNavigationDestinations.fit(order(), slots);
    }

    public static boolean hideLabels(int count, int availableDp) {
        ensure();
        if (!showTitles) return true;
        // Keep labels legible: narrow six-slot docks use icons until space is sufficient.
        return availableDp / Math.max(1, count) < 72;
    }

    public static boolean labels() {
        ensure();
        return showTitles;
    }

    public static boolean animation() {
        return true;
    }

    public static int heightDp() {
        return 60;
    }

    public static int innerMarginDp() {
        return 2;
    }

    public static int bottomGapDp() {
        return isFloatingDock() ? 9 : 0;
    }

    public static int sideGapDp() {
        return isFloatingDock() ? 10 : 0;
    }

    public static int labelGapDp() {
        return 2;
    }

    public static int iconDp() {
        return 23;
    }

    public static float widthFraction() {
        return 1f;
    }

    public static float radiusDp() {
        return isFloatingDock() ? 29f : 0f;
    }

    public static float damping() {
        return .964f;
    }

    public static float stiffness() {
        return 650f;
    }

    public static int contentPaddingDp() {
        return 3;
    }
}
