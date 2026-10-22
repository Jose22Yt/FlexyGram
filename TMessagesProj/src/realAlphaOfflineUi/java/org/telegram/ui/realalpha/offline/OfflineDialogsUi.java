package org.telegram.ui.realalpha.offline;

import org.telegram.messenger.BuildConfig;
import org.telegram.messenger.BuildVariantPolicy;
import org.telegram.messenger.DiagnosticPolicy;

/** UI policy only: never changes account, transport, permissions or capabilities. */
public final class OfflineDialogsUi {
    private OfflineDialogsUi() {}

    public static boolean isClosedRealAlpha() {
        return "realAlpha".equals(BuildConfig.FLEXYGRAM_VARIANT)
                && "io.github.jose22yt.flexygram.realalpha".equals(BuildConfig.APPLICATION_ID)
                && DiagnosticPolicy.isIsolated()
                && BuildConfig.APP_ID == 0 && "".equals(BuildConfig.APP_HASH)
                && !BuildVariantPolicy.authenticationAllowed()
                && !BuildVariantPolicy.telegramTransportAllowed()
                && !BuildVariantPolicy.pushAllowed()
                && !BuildVariantPolicy.translationAllowed()
                && !BuildVariantPolicy.pluginsAllowed()
                && !BuildVariantPolicy.sessionRestoreAllowed();
    }
}
