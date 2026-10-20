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
    private NavigationEvents.Operation pending, active, pendingRapidTap, activeRapidTap;
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
        boolean rapidTap = previousTap != Long.MIN_VALUE && now >= previousTap
                && now - previousTap <= 250_000_000L;
        previousTap = now;
        cancelPending(true);
        NavigationEvents.Op op = destination == Destination.CONVERSATION ? NavigationEvents.Op.chat_open
                : destination == Destination.BACK && fromConversation ? NavigationEvents.Op.chat_close
                : destination == Destination.LIGHT ? NavigationEvents.Op.theme_light
                : destination == Destination.DARK ? NavigationEvents.Op.theme_dark : null;
        NavigationEvents.Operation event = op == null ? null : events.request(op);
        // A rapid tap is a navigation observation, NOT an instant synthetic presentation.
        NavigationEvents.Operation tap = rapidTap && event != null
                ? events.request(NavigationEvents.Op.rapid_tap) : null;
        pending = event;
        pendingRapidTap = tap;
        queue.submit(() -> {
            pending = null;
            pendingRapidTap = null;
            // A preceding accepted transition may have ended before its endpoint was observed.
            // Never mislabel that as a fast presentation or cancellation of the native animation.
            invalidateActive();
            boolean accepted = host.perform(destination);
            if (event == null) return; // Settings has no operation in Work1's v1 protocol.
            if (!accepted) {
                event.cancel();
                if (tap != null) tap.cancel();
                return;
            }
            event.accept();
            if (tap != null) tap.accept();
            if (paused || closed) {
                event.abandon();
                if (tap != null) tap.abandon();
                return;
            }
            active = event;
            activeRapidTap = tap;
            observe(event);
        });
    }
    private void observe(NavigationEvents.Operation event) {
        final NavigationEvents.Operation tap = activeRapidTap;
        host.observeFrame(visible -> {
            if (active != event || event.terminal()) return;
            if (visible == null || paused || closed) {
                event.abandon();
                if (tap != null) tap.abandon();
            } else if (visible) {
                event.present();
                if (tap != null) tap.present();
            } else {
                event.timeout();
                if (tap != null) tap.timeout();
            }
            active = null;
            activeRapidTap = null;
        });
    }
    private void cancelPending(boolean interrupt) {
        if (pending != null && !pending.terminal()) {
            // Measures cancellation of a queued intent only; NOT cancellation of a native Animator.
            NavigationEvents.Operation cancellation = interrupt
                    ? events.request(NavigationEvents.Op.transition_interrupt) : null;
            if (cancellation != null) cancellation.accept();
            pending.cancel();
            if (pendingRapidTap != null) pendingRapidTap.cancel();
            if (cancellation != null) cancellation.cancel();
        }
        pending = null;
        pendingRapidTap = null;
    }
    private void invalidateActive() {
        host.cancelObservation();
        if (active != null) active.abandon();
        if (activeRapidTap != null) activeRapidTap.abandon();
        active = null;
        activeRapidTap = null;
    }
    void pause() { paused = true; queue.cancel(); cancelPending(false); invalidateActive(); previousTap = Long.MIN_VALUE; }
    void resume() { if (!closed) paused = false; }
    @Override public void close() { pause(); closed = true; queue.close(); }
}
