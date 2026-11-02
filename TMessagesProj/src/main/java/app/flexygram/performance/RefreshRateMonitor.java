/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.app.Activity;
import android.content.Context;
import android.hardware.display.DisplayManager;
import android.os.Handler;
import android.os.Looper;
import android.view.Display;
import org.telegram.messenger.AndroidUtilities;

/** Observe actual display changes only while the activity is resumed. No refresh-mode forcing. */
public final class RefreshRateMonitor implements DisplayManager.DisplayListener {
    private final Activity owner;
    private DisplayManager manager;
    private boolean registered;
    public RefreshRateMonitor(Activity owner) { this.owner = owner; }
    public void start() {
        if (registered) return;
        manager = (DisplayManager) owner.getSystemService(Context.DISPLAY_SERVICE);
        if (manager != null) {
            manager.registerDisplayListener(this, new Handler(Looper.getMainLooper()));
            registered = true;
        }
        update();
    }
    public void stop() {
        if (registered) {
            manager.unregisterDisplayListener(this);
            registered = false;
        }
        manager = null;
    }
    private void update() {
        Display display = owner.getWindowManager().getDefaultDisplay();
        if (display == null) return;
        float rate = display.getRefreshRate();
        if (Float.isFinite(rate) && rate > 0 && rate <= 1000) {
            AndroidUtilities.screenRefreshRate = rate;
            AndroidUtilities.screenRefreshTime = 1000f / rate;
        }
    }
    @Override public void onDisplayChanged(int displayId) {
        if (!registered) return;
        Display display = owner.getWindowManager().getDefaultDisplay();
        if (display != null && display.getDisplayId() == displayId) update();
    }
    @Override public void onDisplayAdded(int displayId) { }
    @Override public void onDisplayRemoved(int displayId) { }
}
