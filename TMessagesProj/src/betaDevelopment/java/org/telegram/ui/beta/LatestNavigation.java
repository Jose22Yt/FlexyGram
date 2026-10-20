package org.telegram.ui.beta;

import java.util.function.BooleanSupplier;

/** UI-thread owned, one frame and one latest request; no timer or unbounded tap queue. */
final class LatestNavigation implements AutoCloseable {
    interface Scheduler {
        void postFrame(Runnable action);
        void cancel(Runnable action);
    }
    private final Scheduler scheduler;
    private final BooleanSupplier busy;
    private Runnable pending;
    private boolean posted;
    private boolean closed;
    private final Runnable frame = this::drain;

    LatestNavigation(Scheduler scheduler, BooleanSupplier busy) {
        this.scheduler = scheduler;
        this.busy = busy;
    }

    void submit(Runnable action) {
        if (closed) return;
        pending = action;
        schedule();
    }

    private void schedule() {
        if (!posted) {
            posted = true;
            scheduler.postFrame(frame);
        }
    }

    private void drain() {
        posted = false;
        if (closed || pending == null) return;
        if (busy.getAsBoolean()) {
            schedule();
            return;
        }
        Runnable action = pending;
        pending = null;
        action.run();
    }

    void cancel() {
        pending = null;
        if (posted) scheduler.cancel(frame);
        posted = false;
    }

    @Override public void close() {
        closed = true;
        cancel();
    }
}
