/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import java.util.concurrent.atomic.AtomicBoolean;

/** At most one queued check. Clear before execution so an overlapping event is never lost. */
public final class CoalescedTask implements Runnable {
    public interface Queue { void post(Runnable task); }
    private final Queue queue;
    private final Runnable action;
    private final AtomicBoolean pending = new AtomicBoolean();
    public CoalescedTask(Queue queue, Runnable action) { this.queue=queue; this.action=action; }
    public void request() {
        if (!pending.compareAndSet(false, true)) return;
        try { queue.post(this); }
        catch (RuntimeException failure) { pending.set(false); throw failure; }
    }
    @Override public void run() { pending.set(false); action.run(); }
}
