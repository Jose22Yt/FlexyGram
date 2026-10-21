package org.telegram.ui.realalpha;

import org.telegram.messenger.BuildConfig;
import org.telegram.messenger.BuildVariantPolicy;
import org.telegram.messenger.DiagnosticPolicy;

/** P1/P2 native UI profile. No preference, Intent or private property can open transport. */
public final class RealAlphaPolicy {
    public static final String APPLICATION_ID = "io.github.jose22yt.flexygram.realalpha";

    private RealAlphaPolicy() {}

    public static void requireClosedBuild() {
        if (!APPLICATION_ID.equals(BuildConfig.APPLICATION_ID)
                || !"realAlpha".equals(BuildConfig.FLEXYGRAM_VARIANT)
                || !BuildConfig.FLEXYGRAM_POLICY_SCOPE.matches("[a-f0-9]{64}:realAlpha")
                || !DiagnosticPolicy.isIsolated() || BuildConfig.APP_ID != 0
                || !"".equals(BuildConfig.APP_HASH)
                || BuildVariantPolicy.authenticationAllowed()
                || BuildVariantPolicy.telegramTransportAllowed()
                || BuildVariantPolicy.pushAllowed()
                || BuildVariantPolicy.translationAllowed()
                || BuildVariantPolicy.pluginsAllowed()
                || BuildVariantPolicy.sessionRestoreAllowed()) {
            throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_CLOSED_PROFILE_REQUIRED");
        }
    }
}
