package io.github.jose22yt.flexygram.session;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/** Variant-bound coordinator. Only local adapters are supplied; real Telegram remains denied. */
public final class RequestCoordinator implements AutoCloseable {
    public enum Operation { REQUEST_CODE, VERIFY_CODE, LOGOUT, REVOKE_CURRENT, REVOKE_OTHERS, RESET_ALL_SESSIONS }
    public enum Kind { CODE_SENT, LOCAL_SESSION, ERROR, CANCELLED, DENIED }
    public enum Fault { NONE, INITIALIZATION, INVALID_SCOPE, INVALID_STATE, ADAPTER,
        PROTOCOL, STORAGE, STORAGE_UNCERTAIN, EXISTING_SESSION, CONFLICT, CANCELLED, DENIED }
    public interface Cancellation { void cancel(); }
    public interface Listener { void complete(Reply reply); }
    public enum Domain { LOCAL_SIMULATION, TELEGRAM }
    public interface TransportPort {
        /** Compile-time adapter identity, never a preference or remote switch. */
        Domain domain();
        SessionScope scope();
        void initialize();
        /** Release this flow only; never log out, revoke keys, or close another flow/account. */
        void close();
        /** Exactly one local callback; no retries/fallback. Do not retain input copies after completion. */
        Cancellation submit(Attempt attempt, Listener callback);
    }
    public static final class Input implements AutoCloseable {
        private char[] primary;
        private char[] secondary;
        public Input(char[] primary, char[] secondary) {
            if (primary == null || secondary == null || primary.length > 4096 || secondary.length > 4096) {
                throw new IllegalArgumentException("INVALID_LOCAL_INPUT");
            }
            this.primary = primary.clone(); this.secondary = secondary.clone();
        }
        public synchronized char[] primaryCopy() { requireOpen(); return primary.clone(); }
        public synchronized char[] secondaryCopy() { requireOpen(); return secondary.clone(); }
        public synchronized boolean isClosed() { return primary == null; }
        private void requireOpen() { if (primary == null) throw new IllegalStateException("INPUT_CLOSED"); }
        @Override public synchronized void close() {
            if (primary != null) { Arrays.fill(primary, '\0'); Arrays.fill(secondary, '\0'); primary = secondary = null; }
        }
        @Override public String toString() { return "LocalInput[REDACTED]"; }
    }
    public static final class Reply implements AutoCloseable {
        public final Kind kind;
        public final Fault fault;
        private char[] material;
        private Reply(Kind kind, Fault fault, char[] material) {
            if (material == null || material.length > 4096) throw new IllegalArgumentException("INVALID_LOCAL_REPLY");
            this.kind = kind; this.fault = fault; this.material = material.clone();
        }
        public static Reply codeSent(char[] challenge) { return new Reply(Kind.CODE_SENT, Fault.NONE, challenge); }
        public static Reply localSession(char[] session) { return new Reply(Kind.LOCAL_SESSION, Fault.NONE, session); }
        public static Reply failure(Fault fault) {
            if (fault == null || fault == Fault.NONE) throw new IllegalArgumentException("FAULT_REQUIRED");
            return new Reply(Kind.ERROR, fault, new char[0]);
        }
        private static Reply cancelled() { return new Reply(Kind.CANCELLED, Fault.CANCELLED, new char[0]); }
        private static Reply denied() { return new Reply(Kind.DENIED, Fault.DENIED, new char[0]); }
        public synchronized char[] materialCopy() {
            if (material == null) throw new IllegalStateException("REPLY_CLOSED");
            return material.clone();
        }
        public synchronized boolean isClosed() { return material == null; }
        @Override public synchronized void close() { if (material != null) { Arrays.fill(material, '\0'); material = null; } }
        @Override public String toString() { return "LocalReply[" + kind + "," + fault + "]"; }
    }
    public static final class Ticket {
        private final Object owner;
        public final long id;
        private Ticket(Object owner, long id) { this.owner = owner; this.id = id; }
        @Override public String toString() { return "LocalTicket[" + id + "]"; }
    }
    public static final class Attempt {
        public final SessionScope scope;
        public final Operation operation;
        public final long id;
        public final Input input;
        private Attempt(SessionScope scope, Operation operation, long id, Input input) {
            this.scope = scope; this.operation = operation; this.id = id; this.input = input;
        }
        @Override public String toString() { return "LocalAttempt[" + operation + "," + id + "]"; }
    }
    private static final class Entry {
        final Ticket ticket;
        final Attempt attempt;
        final Listener listener;
        boolean dispatching = true, done, cancelled;
        Cancellation cancellation;
        Reply pending;
        Entry(Ticket ticket, Attempt attempt, Listener listener) { this.ticket=ticket; this.attempt=attempt; this.listener=listener; }
    }
    private enum State { NEW, INITIALIZING, READY, FAILED, CLOSED }
    private State state = State.NEW;
    private final Object owner = new Object();
    private final SessionScope scope;
    private final ClosedRuntime runtime;
    private final TransportPort transport;
    private final Map<Long, Entry> active = new HashMap<>();
    private long nextId;
    private boolean ownsTransport, transportClosed;
    private int listenerFailures, adapterFailures, discardedReplies;
    public RequestCoordinator(ClosedRuntime runtime, TransportPort transport) {
        if (runtime == null || transport == null) throw new IllegalArgumentException("SCOPED_ADAPTER_REQUIRED");
        this.runtime=runtime; this.scope=runtime.scope; this.transport=transport;
    }
    private boolean permitsDomain(ClosedRuntime.Operation operation) {
        Domain domain=transport.domain();
        return domain == Domain.LOCAL_SIMULATION || (domain == Domain.TELEGRAM
                && runtime.authorize(operation) != ClosedRuntime.Decision.DENIED);
    }
    public SessionScope scope() { return scope; }
    public boolean initialize() {
        synchronized (this) {
            if (state == State.READY) return true;
            if (state != State.NEW) return false;
            state=State.INITIALIZING;
        }
        boolean ok=false;
        try { if (permitsDomain(ClosedRuntime.Operation.INITIALIZE_MTPROTO) && scope.equals(transport.scope())) { synchronized(this) { ownsTransport=true; } transport.initialize(); ok=true; } }
        catch (RuntimeException | LinkageError failure) { synchronized(this) { adapterFailures++; } }
        boolean accepted;
        synchronized(this) {
            accepted=state == State.INITIALIZING && ok;
            if (state == State.INITIALIZING) state=ok ? State.READY : State.FAILED;
        }
        if (!accepted) closeTransport();
        return accepted;
    }
    /** Transfers input ownership, including rejection. Replies are borrowed only during complete(). */
    public Ticket submit(SessionScope requestedScope, Operation operation, Input input, Listener listener) {
        if (input == null || listener == null) {
            if (input != null) input.close();
            throw new IllegalArgumentException("LOCAL_REQUEST_REQUIRED");
        }
        Entry entry;
        Fault rejection=null;
        synchronized(this) {
            if (!scope.equals(requestedScope)) rejection=Fault.INVALID_SCOPE;
            else if (operation != Operation.REQUEST_CODE && operation != Operation.VERIFY_CODE) rejection=Fault.DENIED;
            else if (state != State.READY || input.isClosed() || nextId == Long.MAX_VALUE) rejection=Fault.INVALID_STATE;
            if (rejection == null) {
                try {
                    if (!permitsDomain(operation == Operation.REQUEST_CODE
                            ? ClosedRuntime.Operation.REQUEST_CODE : ClosedRuntime.Operation.VERIFY_CODE)) rejection=Fault.DENIED;
                } catch (RuntimeException | LinkageError unavailable) { adapterFailures++; rejection=Fault.ADAPTER; }
            }
            if (rejection != null) entry=null;
            else {
                Ticket ticket=new Ticket(owner, ++nextId);
                entry=new Entry(ticket,new Attempt(scope,operation,ticket.id,input),listener);
                active.put(ticket.id,entry);
            }
        }
        if (entry == null) {
            input.close(); deliver(listener,rejection==Fault.DENIED ? Reply.denied() : Reply.failure(rejection));
            return null;
        }
        Cancellation cancellation=null;
        boolean failed=false;
        try { cancellation=transport.submit(entry.attempt, reply -> accept(entry,reply)); }
        catch (RuntimeException | LinkageError failure) { failed=true; synchronized(this) { adapterFailures++; } }
        Reply result=null;
        boolean cancel=false;
        synchronized(this) {
            entry.dispatching=false;
            entry.cancellation=cancellation;
            if (entry.done) { cancel=entry.cancelled; dispose(entry.pending); entry.pending=null; }
            else if (failed || cancellation == null) {
                dispose(entry.pending); entry.pending=null; result=Reply.failure(Fault.ADAPTER);
            } else { result=entry.pending; entry.pending=null; }
            if (result != null) {
                // Reserve the buffered first reply before releasing the lock. A later callback cannot win.
                entry.done=true; active.remove(entry.ticket.id); entry.attempt.input.close();
            }
        }
        if (cancel) cancelHandle(cancellation);
        if (result != null) deliver(entry.listener,result);
        return entry.ticket;
    }
    private void accept(Entry entry, Reply supplied) {
        Reply reply=supplied;
        if (reply == null) reply=Reply.failure(Fault.PROTOCOL);
        Listener listener=null;
        synchronized(this) {
            if (entry.done) { discardedReplies++; dispose(reply); return; }
            if (entry.dispatching) {
                if (entry.pending == null) entry.pending=reply;
                else { discardedReplies++; if (entry.pending != reply) dispose(reply); }
                return;
            }
            entry.done=true; active.remove(entry.ticket.id); entry.attempt.input.close(); listener=entry.listener;
        }
        deliver(listener,reply);
    }
    public boolean cancel(Ticket ticket) {
        Entry entry;
        Cancellation cancellation;
        synchronized(this) {
            if (ticket == null || ticket.owner != owner || (entry=active.get(ticket.id)) == null) return false;
            entry.done=true; entry.cancelled=true; active.remove(ticket.id);
            entry.attempt.input.close(); dispose(entry.pending); entry.pending=null;
            cancellation=entry.cancellation;
        }
        cancelHandle(cancellation); deliver(entry.listener,Reply.cancelled()); return true;
    }
    private void cancelHandle(Cancellation cancellation) {
        if (cancellation == null) return;
        try { cancellation.cancel(); }
        catch (RuntimeException | LinkageError failure) { synchronized(this) { adapterFailures++; } }
    }
    private void deliver(Listener listener, Reply reply) {
        try { listener.complete(reply); }
        catch (RuntimeException | LinkageError failure) { synchronized(this) { listenerFailures++; } }
        finally { dispose(reply); }
    }
    private static void dispose(Reply reply) { if (reply != null) reply.close(); }
    public synchronized int activeCount() { return active.size(); }
    public synchronized int listenerFailures() { return listenerFailures; }
    public synchronized int adapterFailures() { return adapterFailures; }
    public synchronized int discardedReplies() { return discardedReplies; }
    @Override public void close() {
        Ticket[] tickets;
        boolean defer;
        synchronized(this) {
            if (state == State.CLOSED) return;
            defer=state == State.INITIALIZING;
            state=State.CLOSED;
            tickets=new Ticket[active.size()];
            int index=0;
            for (Entry entry:active.values()) tickets[index++]=entry.ticket;
        }
        for (Ticket ticket:tickets) cancel(ticket);
        if (!defer) closeTransport();
    }
    private void closeTransport() {
        synchronized(this) {
            if (!ownsTransport || transportClosed) return;
            transportClosed=true;
        }
        try { transport.close(); }
        catch (RuntimeException | LinkageError failure) { synchronized(this) { adapterFailures++; } }
    }
}
