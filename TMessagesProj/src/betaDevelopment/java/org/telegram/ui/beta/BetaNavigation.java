package org.telegram.ui.beta;

import java.util.function.Consumer;

/** UI-only intents. The observer never decides whether navigation may run. */
final class BetaNavigation implements AutoCloseable {
    enum Destination { CONVERSATION, SETTINGS, BACK, LIGHT, DARK }
    interface Host {
        boolean busy();
        boolean perform(Destination destination);
        // true = endpoint; false = actual observer deadline; null = observation invalidated.
        void observeFrame(Consumer<Boolean> completion);
        void cancelObservation();
    }
    private final Host host;
    private final LatestNavigation queue;
    private final NavigationEvents events;
    private NavigationEvents.Operation pending, active;
    private boolean paused, closed;
    private long previousTap = Long.MIN_VALUE;

    BetaNavigation(LatestNavigation.Scheduler scheduler, Host host, NavigationEvents events) {
        this.host = host; this.events = events;
        queue = new LatestNavigation(scheduler, host::busy);
    }
    void startup() {
        active = events.request(NavigationEvents.Op.startup); active.accept(); observe(active);
    }
    void request(Destination destination, boolean fromConversation) {
        if (paused || closed) return;
        long now = events.now();
        if (previousTap != Long.MIN_VALUE && now >= previousTap && now - previousTap <= 250_000_000L)
            events.instant(NavigationEvents.Op.rapid_tap);
        previousTap = now;
        cancelPending(true);
        NavigationEvents.Op op = destination == Destination.CONVERSATION ? NavigationEvents.Op.chat_open
                : destination == Destination.BACK && fromConversation ? NavigationEvents.Op.chat_close
                : destination == Destination.LIGHT ? NavigationEvents.Op.theme_light
                : destination == Destination.DARK ? NavigationEvents.Op.theme_dark : null;
        NavigationEvents.Operation event = op == null ? null : events.request(op);
        pending = event;
        queue.submit(() -> {
            pending = null;
            // A preceding accepted transition may have ended before its endpoint was observed.
            // Never mislabel that as a fast presentation or cancellation of the native animation.
            invalidateActive();
            boolean accepted = host.perform(destination);
            if (event == null) return; // Settings has no operation in Work1's v1 protocol.
            if (!accepted) { event.cancel(); return; }
            event.accept();
            if (paused || closed) { event.abandon(); return; }
            active = event; observe(event);
        });
    }
    private void observe(NavigationEvents.Operation event) {
        host.observeFrame(visible -> {
            if (active != event || event.terminal()) return;
            if (visible == null || paused || closed) event.abandon();
            else if (visible) event.present(); else event.timeout();
            active = null;
        });
    }
    private void cancelPending(boolean interrupt) {
        if (pending != null && !pending.terminal()) {
            pending.cancel();
            if (interrupt) events.instant(NavigationEvents.Op.transition_interrupt);
        }
        pending = null;
    }
    private void invalidateActive() {
        host.cancelObservation();
        if (active != null) active.abandon();
        active = null;
    }
    void pause() { paused = true; queue.cancel(); cancelPending(false); invalidateActive(); previousTap = Long.MIN_VALUE; }
    void resume() { if (!closed) paused = false; }
    @Override public void close() { pause(); closed = true; queue.close(); }
}
