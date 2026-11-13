/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.glass;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.graphics.drawable.Drawable;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LiteMode;

/** One material owner per surface. Legacy preferences are retained for the OFF transition. */
public final class IosGlassConfig {
    public static final int HOME = 1, COMPOSER = 2, HEADER = 4, FOLDERS = 8, ALL = 15;
    public static final String FILE = "flexy_ios_glass";
    private static SharedPreferences preferences;
    private static boolean enabled;
    private static int surfaces = ALL;
    private static int revision;
    private static final ArrayList<WeakReference<Drawable>> drawables = new ArrayList<>();
    private static final app.flexygram.performance.CoalescedTask refresh =
            new app.flexygram.performance.CoalescedTask(AndroidUtilities::runOnUIThread, IosGlassConfig::refreshDrawables);
    private static final SharedPreferences.OnSharedPreferenceChangeListener listener = (p, key) -> {
        enabled = p.getBoolean("enabled", false);
        surfaces = p.getInt("surfaces", ALL) & ALL;
        revision++;
        refresh.request();
    };
    private IosGlassConfig() {}
    private static SharedPreferences preferences() {
        if (preferences == null && ApplicationLoader.applicationContext != null) {
            preferences = ApplicationLoader.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE);
            enabled = preferences.getBoolean("enabled", false);
            surfaces = preferences.getInt("surfaces", ALL) & ALL;
            preferences.registerOnSharedPreferenceChangeListener(listener);
        }
        return preferences;
    }
    public static boolean enabled() { preferences(); return enabled; }
    public static boolean selected(int surface) { preferences(); return (surfaces & surface) != 0; }
    public static boolean requested(int surface) { return surface != 0 && enabled() && selected(surface); }
    public static boolean supported() { return Build.VERSION.SDK_INT >= 33; }
    public static boolean active(int surface) {
        return requested(surface) && supported() && !LiteMode.isPowerSaverApplied();
    }
    public static boolean backdrop(int surface, boolean legacy) {
        return supported() && requested(surface) ? active(surface) : legacy;
    }
    public static boolean anyActive() { return active(ALL); }
    public static boolean homeBackdrop(boolean legacy) {
        return backdrop(HOME, legacy) || backdrop(FOLDERS, legacy);
    }
    public static boolean chatBackdrop(boolean legacy) {
        return backdrop(COMPOSER, false) || backdrop(HEADER, legacy);
    }
    public static int revision() { preferences(); return revision; }
    public static void setEnabled(boolean value) {
        SharedPreferences p = preferences();
        if (p != null) p.edit().putBoolean("enabled", value).apply();
    }
    public static void setSelected(int surface, boolean value) {
        SharedPreferences p = preferences();
        if (p != null) p.edit().putInt("surfaces", value ? surfaces | (surface & ALL) : surfaces & ~surface).apply();
    }
    public static void track(Drawable drawable) {
        for (int i = drawables.size() - 1; i >= 0; i--) {
            Drawable current = drawables.get(i).get();
            if (current == null) drawables.remove(i);
            else if (current == drawable) return;
        }
        drawables.add(new WeakReference<>(drawable));
    }
    private static void refreshDrawables() {
        for (int i = drawables.size() - 1; i >= 0; i--) {
            Drawable drawable = drawables.get(i).get();
            if (drawable == null) drawables.remove(i);
            else {
                if (drawable instanceof org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable) {
                    ((org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable)drawable).updateColors();
                }
                drawable.invalidateSelf();
            }
        }
    }
}
