package org.telegram.messenger;

/** Immutable build capabilities, never delegated to preferences, plugins or remote configuration. */
public final class BuildVariantPolicy {
    private BuildVariantPolicy() {}
    public static boolean authenticationAllowed() { return BuildConfig.FLEXYGRAM_CAP_AUTHENTICATION; }
    public static boolean telegramTransportAllowed() { return BuildConfig.FLEXYGRAM_CAP_TELEGRAMTRANSPORT; }
    public static boolean pushAllowed() { return BuildConfig.FLEXYGRAM_CAP_PUSH; }
    public static boolean translationAllowed() { return BuildConfig.FLEXYGRAM_CAP_TRANSLATION; }
    public static boolean pluginsAllowed() { return BuildConfig.FLEXYGRAM_CAP_PLUGINS; }
    public static boolean sessionRestoreAllowed() { return BuildConfig.FLEXYGRAM_CAP_SESSIONRESTORE; }
    public static String storageNamespace() { return BuildConfig.APPLICATION_ID; }
}
