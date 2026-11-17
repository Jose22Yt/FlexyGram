package app.flexygram.performance;

import android.os.MessageQueue;
import java.util.function.BooleanSupplier;

/** One optional dispatch after usable content and an idle main queue; never polls or forces draws.
 * All methods and the readiness predicate belong to the UI thread. Close with the Activity.
 */
public final class StartupIdleWork implements AutoCloseable {
    private final MessageQueue queue;
    private final BooleanSupplier ready;
    private final Runnable work;
    private boolean scheduled, complete;
    private final MessageQueue.IdleHandler idle = this::onIdle;

    public StartupIdleWork(MessageQueue queue, BooleanSupplier ready, Runnable work) {
        this.queue = queue;
        this.ready = ready;
        this.work = work;
    }

    public void afterDraw() {
        if (complete || scheduled || !ready.getAsBoolean()) return;
        scheduled = true;
        queue.addIdleHandler(idle);
    }

    private boolean onIdle() {
        scheduled = false;
        if (!complete && ready.getAsBoolean()) {
            complete = true;
            work.run(); // Dispatch only; heavy work must stay on its existing worker.
        }
        return false;
    }

    @Override public void close() {
        complete = true;
        scheduled = false;
        queue.removeIdleHandler(idle);
    }
}
