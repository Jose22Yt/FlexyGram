package org.telegram.ui.beta;

/** Process-local beta post-init result; never restored from Bundle and never logs exceptions. */
final class BetaPostInit {
    private enum State { NEW, RUNNING, READY, FAILED }
    private static State state = State.NEW;

    private BetaPostInit() { }

    static synchronized boolean ensure(Runnable initialize) {
        if (state == State.READY) return true;
        // ApplicationLoader sets its own initialized flag before all work completes.
        // Neither a retry after failure nor synchronous reentry proves completion.
        if (state != State.NEW) return false;
        state = State.RUNNING;
        try {
            initialize.run();
            state = State.READY;
            return true;
        } catch (RuntimeException | LinkageError initializationFailure) {
            state = State.FAILED;
            return false;
        } finally {
            // Other fatal Errors still propagate, but cannot leave a retryable partial process.
            if (state == State.RUNNING) state = State.FAILED;
        }
    }
}
