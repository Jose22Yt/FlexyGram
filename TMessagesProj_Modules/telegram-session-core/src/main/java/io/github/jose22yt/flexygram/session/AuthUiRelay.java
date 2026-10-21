package io.github.jose22yt.flexygram.session;

import java.util.concurrent.Executor;
import io.github.jose22yt.flexygram.session.AuthenticationController.UiSnapshot;

/** Event-driven UI seam. Android adapter must supply its serial main-thread executor. */
public final class AuthUiRelay implements AutoCloseable {
    public interface Observer { void changed(UiSnapshot snapshot); }
    public final class Binding implements AutoCloseable {
        private Executor executor;
        private Observer observer;
        private long delivered=-1;
        private Binding(Executor executor, Observer observer) { this.executor=executor; this.observer=observer; }
        @Override public void close() {
            synchronized(AuthUiRelay.this) {
                observer=null; executor=null;
                if (current == this) current=null;
            }
        }
    }
    private final SessionScope scope;
    private UiSnapshot latest;
    private Binding current;
    private int observerFailures, executorFailures;
    private boolean closed;
    AuthUiRelay(UiSnapshot initial) {
        if (initial == null) throw new IllegalArgumentException("UI_STATE_REQUIRED");
        scope=initial.scope; latest=initial;
    }
    public Binding attach(Executor executor, Observer observer) {
        if (executor == null || observer == null) throw new IllegalArgumentException("UI_BINDING_REQUIRED");
        Binding binding;UiSnapshot snapshot;long revision;
        synchronized(this) {
            if (closed) throw new IllegalStateException("UI_RELAY_CLOSED");
            if (current != null) current.close();
            binding=new Binding(executor,observer); current=binding;snapshot=latest;revision=latest.revision;
        }
        enqueue(binding,snapshot,revision);return binding;
    }
    void publish(UiSnapshot snapshot) {
        Binding binding;long revision;
        synchronized(this) {
            if (snapshot == null || !scope.equals(snapshot.scope)) throw new IllegalArgumentException("UI_SCOPE_MISMATCH");
            if (closed) return;
            if (snapshot.revision <= latest.revision) return;
            latest=snapshot;revision=snapshot.revision;binding=current;
        }
        if (binding != null) enqueue(binding,snapshot,revision);
    }
    private void enqueue(Binding binding, UiSnapshot snapshot, long revision) {
        Executor executor;
        synchronized(this) { if (closed || binding != current) return;executor=binding.executor; }
        if (executor == null) return;
        try {
            executor.execute(() -> {
                Observer observer;
                synchronized(AuthUiRelay.this) {
                    if (closed || current != binding || binding.observer == null || revision <= binding.delivered) return;
                    binding.delivered=revision; observer=binding.observer;
                }
                try { observer.changed(snapshot); }
                catch (RuntimeException | LinkageError failure) { synchronized(AuthUiRelay.this) { observerFailures++; } }
            });
        } catch (RuntimeException | LinkageError failure) { synchronized(this) { executorFailures++; } }
    }
    public synchronized int observerFailures() { return observerFailures; }
    public synchronized int executorFailures() { return executorFailures; }
    @Override public synchronized void close() {
        if (current != null) current.close();
        closed=true;
    }
}
