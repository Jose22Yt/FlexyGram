package org.telegram.messenger;

import android.os.SystemClock;
import android.text.TextUtils;

import org.unifiedpush.android.connector.UnifiedPush;

import java.util.List;

public class UnifiedPushListenerServiceProvider implements PushListenerController.IPushListenerServiceProvider {
    public UnifiedPushListenerServiceProvider(){}

    @Override
    public boolean hasServices() {
        if (!PushServicesPolicy.unifiedAllowed()) return false;
        return UnifiedPush.getDistributors(ApplicationLoader.applicationContext).contains(PushServicesPolicy.distributor());
    }

    @Override
    public String getLogTitle() {
        return "UnifiedPush";
    }

    @Override
    public void onRequestPushToken() {
        if (!PushServicesPolicy.unifiedAllowed()) return;
        String currentPushString = SharedConfig.pushString;
        if (!TextUtils.isEmpty(currentPushString)) {
            FileLog.d("UnifiedPush registration available");
        } else {
            FileLog.d("No UnifiedPush string found");
        }
        Utilities.globalQueue.postRunnable(() -> {
            try {
                SharedConfig.pushStringGetTimeStart = SystemClock.elapsedRealtime();
                SharedConfig.saveConfig();
                if (!PushServicesPolicy.unifiedAllowed()) return;
                if (!UnifiedPush.getDistributors(ApplicationLoader.applicationContext)
                        .contains(PushServicesPolicy.distributor())) return;
                UnifiedPush.saveDistributor(ApplicationLoader.applicationContext, PushServicesPolicy.distributor());
                UnifiedPush.register(
                        ApplicationLoader.applicationContext,
                        "default",
                        "FlexyGram Push",
                        null
                );
            } catch (Throwable e) {
                FileLog.e("UnifiedPush operation failed (" + e.getClass().getSimpleName() + ")");
            }
        });
    }

    @Override
    public int getPushType() {
        return PushListenerController.PUSH_TYPE_WEB;
    }
}

