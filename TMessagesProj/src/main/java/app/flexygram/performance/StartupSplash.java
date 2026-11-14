/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.app.Activity;
import android.os.Build;

/** Icon-free system starting window, removed on the first available content frame. */
public final class StartupSplash {
    private StartupSplash() { }

    public static void install(Activity activity) {
        if (Build.VERSION.SDK_INT >= 31) {
            activity.getSplashScreen().setOnExitAnimationListener(view -> view.remove());
        }
    }
}
