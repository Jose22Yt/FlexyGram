package org.telegram.ui.beta;

/** Activity-local observations, never serialized as proof of runtime initialization after process death. */
final class ProbeState {
    enum Value { IDLE, RUNNING, READY, FAILED }
    enum Outcome { READY, JNI_UNAVAILABLE, PYTHON_START_FAILED, PYTHON_IMPORT_FAILED }
    private Value value = Value.IDLE;
    private Outcome outcome;
    private boolean closed;
    Value value() { return value; }
    Outcome outcome() { return outcome; }
    boolean begin() {
        if (closed || value == Value.RUNNING) return false;
        outcome = null; value = Value.RUNNING; return true;
    }
    boolean finish(boolean success) { return finish(success ? Outcome.READY : Outcome.PYTHON_IMPORT_FAILED); }
    boolean finish(Outcome result) {
        if (closed) return false;
        outcome = java.util.Objects.requireNonNull(result);
        value = result == Outcome.READY ? Value.READY : Value.FAILED;
        return true;
    }
    void close() { closed = true; }
}
