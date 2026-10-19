package org.telegram.messenger;

/** No preference, resource or SDK fallback can authorize a service. Diagnostic always denies. */
public final class PushServicesPolicy {
    private PushServicesPolicy() {}
    public static boolean fcmAllowed() {
        return configured() && BuildConfig.FLEXYGRAM_FCM_ENABLED
            && BuildConfig.FLEXYGRAM_FCM_PROJECT_ID.matches("flexygram-[a-z0-9-]{1,20}")
            && BuildConfig.FLEXYGRAM_FCM_API_KEY.matches("AIza[A-Za-z0-9_-]{35}")
            && BuildConfig.FLEXYGRAM_FCM_SENDER_ID.matches("[1-9][0-9]{5,19}")
            && BuildConfig.FLEXYGRAM_FCM_APP_ID.startsWith("1:" + BuildConfig.FLEXYGRAM_FCM_SENDER_ID + ":android:");
    }
    public static boolean unifiedAllowed() {
        return configured() && BuildConfig.FLEXYGRAM_UNIFIED_PUSH_ENABLED
            && BuildConfig.FLEXYGRAM_UNIFIED_GATEWAY.startsWith("https://")
            && !BuildConfig.FLEXYGRAM_UNIFIED_DISTRIBUTOR.isEmpty();
    }
    private static boolean configured() {
        return !DiagnosticPolicy.isIsolated()
            && BuildConfig.APPLICATION_ID.startsWith("io.github.jose22yt.flexygram.")
            && !BuildConfig.APPLICATION_ID.equals("io.github.jose22yt.flexygram.diagnostic")
            && BuildConfig.APPLICATION_ID.equals(BuildConfig.FLEXYGRAM_PUSH_ANDROID_ID)
            && BuildConfig.FLEXYGRAM_PUSH_SCOPE.matches("[a-f0-9]{64}");
    }
    public static boolean anyAllowed() { return fcmAllowed() || unifiedAllowed(); }
    public static boolean isTypeAllowed(int type) {
        if (type == 2) return fcmAllowed();
        if (type == 4 || type == 10) return unifiedAllowed();
        return false; // Includes the unsupported Huawei provider: never borrow a fallback.
    }
    public static String scope() { return anyAllowed() ? BuildConfig.FLEXYGRAM_PUSH_SCOPE : ""; }
    public static String unifiedGateway() { return unifiedAllowed() ? BuildConfig.FLEXYGRAM_UNIFIED_GATEWAY : ""; }
    public static String distributor() { return unifiedAllowed() ? BuildConfig.FLEXYGRAM_UNIFIED_DISTRIBUTOR : ""; }
    public static boolean crashReportingAllowed() { return false; } // Separate service, not authorized by FCM.
}
