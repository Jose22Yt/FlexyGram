package app.exteraless.proxy;

import android.os.SystemClock;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.SharedConfig;
import org.telegram.messenger.UserConfig;
import org.telegram.tgnet.ConnectionsManager;

/** A proxy-status timer exists only while a proxy is enabled. All ownership stays on UI. */
public final class ProxyPingController implements NotificationCenter.NotificationCenterDelegate {
    private static final long INTERVAL_MS = 10_000L;
    private static final ProxyPingController INSTANCE = new ProxyPingController();
    private static final Runnable PING = ProxyPingController::ping;
    private boolean initialized;

    private ProxyPingController() { }

    public static void init() {
        AndroidUtilities.runOnUIThread(INSTANCE::initialize);
    }

    private void initialize() {
        if (initialized) return;
        initialized = true;
        NotificationCenter.getGlobalInstance().addObserver(this, NotificationCenter.proxySettingsChanged);
        // The native isProxyEnabled() also decodes the saved proxy list. Keep that out of startup.
        if (enabledInPreferences()) AndroidUtilities.runOnUIThread(PING, INTERVAL_MS);
    }

    @Override public void didReceivedNotification(int id, int account, Object... args) {
        if (id == NotificationCenter.proxySettingsChanged) schedule();
    }

    private static void ping() {
        boolean enabled = enabledInPreferences() && SharedConfig.isProxyEnabled();
        SharedConfig.ProxyInfo proxy = SharedConfig.currentProxy;
        if (enabled && proxy != null) {
            int ping = ConnectionsManager.native_getCurrentPingTime(UserConfig.selectedAccount);
            if (ping > 0) {
                proxy.ping = ping;
                proxy.available = true;
                proxy.availableCheckTime = SystemClock.elapsedRealtime();
                NotificationCenter.getGlobalInstance().postNotificationName(NotificationCenter.proxyPingUpdated, ping);
            }
        }
        schedule();
    }

    private static boolean enabledInPreferences() {
        return MessagesController.getGlobalMainSettings().getBoolean("proxy_enabled", false);
    }

    private static void schedule() {
        AndroidUtilities.cancelRunOnUIThread(PING);
        if (enabledInPreferences() && SharedConfig.currentProxy != null)
            AndroidUtilities.runOnUIThread(PING, INTERVAL_MS);
    }
}
