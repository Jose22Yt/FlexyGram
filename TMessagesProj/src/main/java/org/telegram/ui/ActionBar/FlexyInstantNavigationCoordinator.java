/* SPDX-License-Identifier: GPL-3.0-or-later */
package org.telegram.ui.ActionBar;

/**
 * Thread-confined logical navigation ownership. No clocks, queues, Views or retained callbacks.
 * Hosts report accepted native operations; interruption still requires their visibility/modal policy.
 */
public final class FlexyInstantNavigationCoordinator {
    public enum State { IDLE, OPENING, CLOSING, DRAGGING, SETTLING, COMMITTING, CANCELLED }
    public enum Kind { OPEN_CHAT, OPEN_SCREEN, BACK, REVEAL_SURFACE, MODAL }

    public static final class Intent {
        public final Kind kind;
        public final long destinationId;
        public final String screenName;

        public Intent(Kind kind, long destinationId, String screenName) {
            if (kind == null) throw new IllegalArgumentException("intent kind");
            this.kind = kind;
            this.destinationId = destinationId;
            this.screenName = screenName;
        }
    }

    private final Thread ownerThread = Thread.currentThread();
    private long generation;
    private State state = State.IDLE;
    private Intent intent;
    private boolean interruptible;

    private void checkThread() {
        if (Thread.currentThread() != ownerThread) throw new IllegalStateException("navigation thread");
    }

    public long generation() { checkThread(); return generation; }
    public State state() { checkThread(); return state; }
    public Intent intent() { checkThread(); return intent; }
    public boolean isCurrent(long ticket) { checkThread(); return ticket == generation; }

    /** Report a new accepted operation, including one accepted reentrantly during a commit. */
    public long begin(State next, Intent nextIntent, boolean mayInterrupt) {
        checkThread();
        if (next == null || next == State.IDLE || next == State.COMMITTING || next == State.CANCELLED || nextIntent == null) {
            throw new IllegalArgumentException("accepted navigation operation");
        }
        generation++;
        state = next;
        intent = nextIntent;
        interruptible = mayInterrupt;
        return generation;
    }

    /** Native visual completion must never finish a newer operation or an active commit. */
    public boolean complete(long ticket) {
        checkThread();
        if (ticket != generation || state == State.IDLE || state == State.CANCELLED || state == State.COMMITTING) return false;
        clear(State.IDLE);
        return true;
    }

    public boolean cancel(long ticket) {
        checkThread();
        if (ticket != generation || state == State.IDLE || state == State.CANCELLED) return false;
        generation++;
        clear(State.CANCELLED);
        return true;
    }

    /**
     * Execute an already-approved native finalization exactly once. Never queues or replays it.
     * If the callback accepts a newer operation, its ownership survives this older transaction.
     */
    public boolean commit(long ticket, Runnable nativeFinalization) {
        checkThread();
        if (nativeFinalization == null) throw new IllegalArgumentException("native finalization");
        if (ticket != generation || !interruptible ||
                (state != State.OPENING && state != State.CLOSING && state != State.SETTLING)) return false;
        state = State.COMMITTING;
        interruptible = false;
        try {
            nativeFinalization.run();
        } catch (RuntimeException | Error failure) {
            if (ticket == generation) {
                generation++;
                clear(State.CANCELLED);
            }
            throw failure;
        }
        if (ticket != generation) return false;
        clear(State.IDLE);
        return true;
    }

    private void clear(State result) {
        state = result;
        intent = null;
        interruptible = false;
    }
}
