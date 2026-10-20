package org.telegram.ui.beta;

import java.io.IOException;
import java.io.Writer;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReferenceArray;
import java.util.function.LongSupplier;

/** Single UI producer / single exporter. Bounded, no locks, disk, Logcat or navigation data on UI. */
final class NavigationEvents {
    enum Op { startup, chat_open, chat_close, rapid_tap, transition_interrupt, theme_light, theme_dark }
    private static final AtomicLong sessions = new AtomicLong();
    private final String session = "b" + Long.toUnsignedString(sessions.incrementAndGet(), 36)
            + "_" + Long.toUnsignedString(System.nanoTime(), 36);
    private final AtomicReferenceArray<String> ring;
    private final AtomicLong written = new AtomicLong(), read = new AtomicLong(), lost = new AtomicLong();
    private final LongSupplier clock;
    private final Thread producer = Thread.currentThread();
    private long sequence, lastTime;
    private final AtomicLong abandoned = new AtomicLong();
    private final AtomicBoolean draining = new AtomicBoolean();

    NavigationEvents(int capacity, LongSupplier clock) {
        if (capacity < 1) throw new IllegalArgumentException("Invalid observer capacity");
        ring = new AtomicReferenceArray<>(capacity);
        this.clock = clock;
    }

    final class Operation {
        final String id;
        final Op op;
        private boolean accepted, terminal;
        private Operation(Op op) { this.id = session + "_" + Long.toUnsignedString(++sequence, 36); this.op = op; }
        boolean terminal() { return terminal; }
        void accept() { ui(); if (!accepted && !terminal) { accepted = true; emit(this, "accepted"); } }
        void present() { ui(); if (accepted && !terminal) { terminal = true; emit(this, "presented"); } }
        void cancel() { end("cancelled"); }
        void timeout() { end("timeout"); }
        void abandon() { ui(); if (!terminal) { terminal = true; abandoned.incrementAndGet(); } }
        private void end(String phase) { ui(); if (!terminal) { terminal = true; emit(this, phase); } }
    }

    Operation request(Op op) { ui(); Operation event = new Operation(op); emit(event, "request"); return event; }
    void instant(Op op) { Operation event = request(op); event.accept(); event.present(); }
    long now() { ui(); return clock.getAsLong(); }
    String session() { return session; }
    long lostEvents() { return lost.get(); }
    long abandonedOperations() { return abandoned.get(); }
    void exportFailed(long records) { lost.addAndGet(records); }
    private void ui() {
        if (Thread.currentThread() != producer) throw new IllegalStateException("UI observer ownership required");
    }
    private void emit(Operation event, String phase) {
        long stamp = clock.getAsLong();
        // CLOCK_MONOTONIC is ordered; clock regressions invalidate evidence rather than invent durations.
        if (stamp < 0 || stamp < lastTime) { lost.incrementAndGet(); return; }
        lastTime = stamp;
        long next = written.get();
        if (next - read.get() >= ring.length()) { lost.incrementAndGet(); return; }
        String line = "{\"id\":\"" + event.id + "\",\"op\":\"" + event.op.name()
                + "\",\"phase\":\"" + phase + "\",\"timestamp_ns\":" + stamp
                + ",\"clock\":\"android_monotonic_ns\"}";
        ring.set((int)(next % ring.length()), line);
        written.set(next + 1);
    }

    /** One background consumer only. Drains a fixed boundary, never waits for new UI events. */
    long drainTo(Writer output) throws IOException {
        if (Thread.currentThread() == producer) throw new IllegalStateException("Export must be off UI");
        if (!draining.compareAndSet(false, true)) throw new IllegalStateException("One exporter required");
        long boundary = written.get(), count = 0;
        try {
            while (read.get() < boundary) {
                long slot = read.get();
                String line = ring.getAndSet((int)(slot % ring.length()), null);
                read.set(slot + 1);
                if (line == null) { lost.incrementAndGet(); continue; }
                count++;
                output.write(line); output.write('\n');
            }
        } catch (IOException error) {
            lost.addAndGet(count); // no claim of complete export after a failed write
            throw error;
        } finally { draining.set(false); }
        return count;
    }
}
