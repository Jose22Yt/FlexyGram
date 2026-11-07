/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.app.Activity;
import android.os.Build;
import android.view.View;
import java.lang.ref.WeakReference;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.R;
import org.telegram.ui.LauncherIconController;
import org.telegram.ui.LauncherIconController.LauncherIcon;

/** Use Android's starting window, without a second activity, timer, or chat/network readiness gate. */
public final class StartupSplash {
    private static WeakReference<Activity> host = new WeakReference<>(null);
    private static int appliedTheme;
    private static boolean refreshScheduled;

    private StartupSplash() { }

    public static void install(Activity activity) {
        host = new WeakReference<>(activity);
        refreshScheduled = false;
        if (Build.VERSION.SDK_INT >= 31) {
            // Remove the transferred splash as soon as Android has the content frame ready.
            activity.getSplashScreen().setOnExitAnimationListener(view -> view.remove());
        }
    }

    /** Persist the selected theme after drawing, rather than doing a PackageManager call before it. */
    public static void refreshAfterFirstFrame(Activity activity) {
        if (Build.VERSION.SDK_INT < 31 || refreshScheduled) return;
        refreshScheduled = true;
        View decor = activity.getWindow().getDecorView();
        decor.postOnAnimation(() -> decor.post(() -> {
            refreshScheduled = false;
            refresh(activity, LauncherIconController.getRememberedIcon());
        }));
    }

    public static void iconChanged() {
        if (Build.VERSION.SDK_INT < 31) return;
        AndroidUtilities.runOnUIThread(() -> {
            Activity activity = host.get();
            if (activity != null) refreshAfterFirstFrame(activity);
        });
    }

    private static void refresh(Activity activity, LauncherIcon icon) {
        if (Build.VERSION.SDK_INT < 31 || activity.isFinishing() || activity.isDestroyed()) return;
        int theme = themeFor(icon);
        if (theme == appliedTheme) return;
        try {
            // Framework persists the stable resource NAME, so resource ID changes on update are safe.
            activity.getSplashScreen().setSplashScreenTheme(theme);
            appliedTheme = theme;
        } catch (RuntimeException error) {
            // A cosmetic system theme must never prevent the launcher icon change or app startup.
            FileLog.e(error);
        }
    }

    public static int themeFor(LauncherIcon icon) {
        switch (icon) {
            case FLEX_NEON: return R.style.Theme_FlexyGram_Start_FLEX_NEON;
            case FLEX_GLOSSY: return R.style.Theme_FlexyGram_Start_FLEX_GLOSSY;
            case FLEX_COSMIC: return R.style.Theme_FlexyGram_Start_FLEX_COSMIC;
            case FLEX_CYBER: return R.style.Theme_FlexyGram_Start_FLEX_CYBER;
            case EXTERALESS: return R.style.Theme_FlexyGram_Start_EXTERALESS;
            case FLEX_GREEN: return R.style.Theme_FlexyGram_Start_FLEX_GREEN;
            case FLEX_CORAL: return R.style.Theme_FlexyGram_Start_FLEX_CORAL;
            case FLEX_MONO: return R.style.Theme_FlexyGram_Start_FLEX_MONO;
            case FLEX_BLUEPRINT: return R.style.Theme_FlexyGram_Start_FLEX_BLUEPRINT;
            case FLEX_NYA: return R.style.Theme_FlexyGram_Start_FLEX_NYA;
            case FLEX_QUACK: return R.style.Theme_FlexyGram_Start_FLEX_QUACK;
            case FLEX_GO: return R.style.Theme_FlexyGram_Start_FLEX_GO;
            case LEGACY_EXTERALESS: return R.style.Theme_FlexyGram_Start_LEGACY_EXTERALESS;
            case BLUEPRINT: return R.style.Theme_FlexyGram_Start_BLUEPRINT;
            case RED: return R.style.Theme_FlexyGram_Start_RED;
            case NYA: return R.style.Theme_FlexyGram_Start_NYA;
            case AYU: return R.style.Theme_FlexyGram_Start_AYU;
            case QUACK: return R.style.Theme_FlexyGram_Start_QUACK;
            case GO: return R.style.Theme_FlexyGram_Start_GO;
            case HAND: return R.style.Theme_FlexyGram_Start_HAND;
            case MONO: return R.style.Theme_FlexyGram_Start_MONO;
            case NOTHING: return R.style.Theme_FlexyGram_Start_NOTHING;
            case PLUS: return R.style.Theme_FlexyGram_Start_PLUS;
            case TELEGRAM: return R.style.Theme_FlexyGram_Start_TELEGRAM;
            case VINTAGE: return R.style.Theme_FlexyGram_Start_VINTAGE;
            case AQUA: return R.style.Theme_FlexyGram_Start_AQUA;
            case PREMIUM: return R.style.Theme_FlexyGram_Start_PREMIUM;
            case TURBO: return R.style.Theme_FlexyGram_Start_TURBO;
            case NOX: return R.style.Theme_FlexyGram_Start_NOX;
            default: return R.style.Theme_FlexyGram_Start_FLEX_GLOSSY;
        }
    }
}
