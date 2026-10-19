package org.telegram.messenger;

import android.os.SystemClock;
import android.text.TextUtils;

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.messaging.FirebaseMessaging;

public class GooglePushListenerServiceProvider implements PushListenerController.IPushListenerServiceProvider {

    public static volatile String lastError;

    private Boolean hasServices;

    public GooglePushListenerServiceProvider() {}

    @Override
    public String getLogTitle() {
        return "Google Play Services";
    }

    @Override
    public int getPushType() {
        return PushListenerController.PUSH_TYPE_FIREBASE;
    }

    @Override
    public void onRequestPushToken() {
        if (org.telegram.messenger.DiagnosticPolicy.isIsolated()) return;
        if (!PushServicesPolicy.fcmAllowed()) return;
        String currentPushString = SharedConfig.pushString;
        if (!TextUtils.isEmpty(currentPushString)) {
            if (BuildVars.DEBUG_PRIVATE_VERSION) {
                FileLog.d("FCM registration available");
            }
        } else {
            FileLog.d("FCM Registration not found.");
        }
        Utilities.globalQueue.postRunnable(() -> {
            try {
                SharedConfig.pushStringGetTimeStart = SystemClock.elapsedRealtime();
                if (!PushServicesPolicy.fcmAllowed()) return;
                ensureOwnedFirebaseApp();
                FirebaseMessaging.getInstance().getToken()
                        .addOnCompleteListener(task -> {
                            if (!PushServicesPolicy.fcmAllowed()) return;
                            SharedConfig.pushStringGetTimeEnd = SystemClock.elapsedRealtime();
                            if (!task.isSuccessful()) {
                                Exception error = task.getException();
                                lastError = error == null ? "unknown" : error.getClass().getSimpleName();
                                FileLog.d("Failed to get regid: " + lastError);
                                SharedConfig.pushStringStatus = "__FIREBASE_FAILED__";
                                PushListenerController.sendRegistrationToServer(getPushType(), null);
                                ApplicationLoader.startPushService();
                                return;
                            }
                            lastError = null;
                            String token = task.getResult();
                            if (!TextUtils.isEmpty(token)) {
                                PushListenerController.sendRegistrationToServer(getPushType(), token);
                            }
                        });
            } catch (Throwable e) {
                FileLog.e("Google push operation failed (" + e.getClass().getSimpleName() + ")");
            }
        });
    }

    private static synchronized void ensureOwnedFirebaseApp() {
        FirebaseOptions options = new FirebaseOptions.Builder()
            .setProjectId(BuildConfig.FLEXYGRAM_FCM_PROJECT_ID)
            .setApplicationId(BuildConfig.FLEXYGRAM_FCM_APP_ID)
            .setGcmSenderId(BuildConfig.FLEXYGRAM_FCM_SENDER_ID)
            .setApiKey(BuildConfig.FLEXYGRAM_FCM_API_KEY).build();
        FirebaseApp existing;
        try { existing = FirebaseApp.getInstance(); }
        catch (IllegalStateException absent) {
            FirebaseApp.initializeApp(ApplicationLoader.applicationContext, options);
            return;
        }
        if (!ownedOptions(existing.getOptions())) {
            throw new IllegalStateException("Unapproved Firebase application");
        }
    }

    static boolean hasOwnedFirebaseApp() {
        if (!PushServicesPolicy.fcmAllowed()) return false;
        try { return ownedOptions(FirebaseApp.getInstance().getOptions()); }
        catch (IllegalStateException absent) { return false; }
    }

    private static boolean ownedOptions(FirebaseOptions options) {
        return BuildConfig.FLEXYGRAM_FCM_PROJECT_ID.equals(options.getProjectId())
            && BuildConfig.FLEXYGRAM_FCM_APP_ID.equals(options.getApplicationId())
            && BuildConfig.FLEXYGRAM_FCM_SENDER_ID.equals(options.getGcmSenderId())
            && BuildConfig.FLEXYGRAM_FCM_API_KEY.equals(options.getApiKey());
    }

    @Override
    public boolean hasServices() {
        if (!PushServicesPolicy.fcmAllowed()) return false;
        if (hasServices == null) {
            try {
                int resultCode = GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(ApplicationLoader.applicationContext);
                hasServices = resultCode == ConnectionResult.SUCCESS;
            } catch (Exception e) {
                FileLog.e("Google push operation failed (" + e.getClass().getSimpleName() + ")");
                hasServices = false;
            }
        }
        return hasServices;
    }
}

