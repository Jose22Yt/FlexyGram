/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.os.SystemClock;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.MessagesStorage;
import org.telegram.messenger.SharedConfig;
import org.telegram.messenger.UserConfig;

/** Event-driven idle work: one delayed check, one local read at a time, two candidates per batch. */
public final class ChatHistoryWarmup implements Runnable {
    public interface Host {
        boolean canWarm();
        int account();
        long[] candidates();
    }
    private final Host host;
    private boolean scheduled, busy;
    private long generation, lastBatch = -1;
    private Runnable cancelRead;
    public ChatHistoryWarmup(Host host) { this.host = host; }
    public void request() {
        if (scheduled || busy || !host.canWarm()) return;
        scheduled = true;
        long now = SystemClock.uptimeMillis();
        long delay = lastBatch < 0 || now < lastBatch ? 350 : Math.max(350, 3000 - (now - lastBatch));
        AndroidUtilities.runOnUIThread(this, delay);
    }
    public void cancel() {
        generation++; scheduled = busy = false;
        AndroidUtilities.cancelRunOnUIThread(this);
        Runnable previous = cancelRead; cancelRead = null;
        if (previous != null) previous.run();
    }
    @Override public void run() {
        if (!scheduled) return;
        scheduled = false;
        if (!host.canWarm()) return;
        int account = host.account();
        UserConfig config = UserConfig.getInstance(account);
        long owner = config.getClientUserId();
        if (owner == 0 || !config.isClientActivated()) return;
        long[] candidates = host.candidates();
        if (candidates == null || candidates.length == 0) return;
        busy = true; lastBatch = SystemClock.uptimeMillis();
        next(generation, account, owner, candidates, 0);
    }
    private void next(long token, int account, long owner, long[] candidates, int index) {
        if (token != generation) return;
        if (host.account() != account || !host.canWarm() || !UserConfig.getInstance(account).isClientActivated()
                || UserConfig.getInstance(account).getClientUserId() != owner || index >= Math.min(2, candidates.length)) {
            busy = false; return;
        }
        boolean visible = false;
        long[] current = host.candidates();
        if (current != null) for (long id : current) if (id == candidates[index]) { visible = true; break; }
        if (!visible) { next(token, account, owner, candidates, index + 1); return; }
        cancelRead = MessagesStorage.getInstance(account).warmChatHistory(candidates[index], SharedConfig.deviceIsHigh() ? 25 : 15, () -> {
            if (token != generation) return;
            cancelRead = null;
            next(token, account, owner, candidates, index + 1);
        });
    }
}
