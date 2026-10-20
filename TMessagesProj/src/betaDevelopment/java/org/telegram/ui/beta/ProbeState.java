package org.telegram.ui.beta;

/** Activity-owned local runtime result. Recreated views read state, never receive stale cell callbacks. */
final class ProbeState {
    enum Value { IDLE, RUNNING, READY, FAILED }
    private Value value = Value.IDLE;
    private boolean closed;
    Value value() { return value; }
    boolean begin() { if (closed || value == Value.RUNNING) return false; value = Value.RUNNING; return true; }
    boolean finish(boolean success) { if (closed) return false; value = success ? Value.READY : Value.FAILED; return true; }
    void close() { closed = true; }
}
