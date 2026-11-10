/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import java.util.function.BooleanSupplier;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ChatActivity;

/** UI-owned request generation. Disk completion never revives an obsolete navigation. */
public final class ChatNavigationGate {
    private long generation;
    public void cancel() { generation++; }

    public boolean defer(BaseFragment fragment, BooleanSupplier ownerValid, Runnable resume, Runnable failed) {
        final long ticket = ++generation;
        if (!(fragment instanceof ChatActivity)) return false;
        final int account = fragment.getCurrentAccount(), selected = UserConfig.selectedAccount;
        return ChatPeerPreloader.prepare(account, fragment.getArguments(), found -> {
            if (ticket != generation || fragment.isFinished || fragment.getCurrentAccount() != account
                    || UserConfig.selectedAccount != selected || !ownerValid.getAsBoolean()) return;
            if (found) resume.run(); else failed.run();
        });
    }
}
