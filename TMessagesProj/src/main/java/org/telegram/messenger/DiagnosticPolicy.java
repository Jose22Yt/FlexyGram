package org.telegram.messenger;

/** Fail-closed diagnostic policy. Enabling networking requires a reviewed code change. */
public final class DiagnosticPolicy {
    private DiagnosticPolicy() {}
    public static boolean isIsolated() { return BuildConfig.ISOLATED_DIAGNOSTIC; }
}
