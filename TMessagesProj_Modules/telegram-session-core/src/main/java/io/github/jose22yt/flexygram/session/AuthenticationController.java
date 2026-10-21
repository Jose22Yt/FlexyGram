package io.github.jose22yt.flexygram.session;

import java.util.Arrays;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;

/** Two-phase LOCAL auth contract. No Android, TLRPC, account activation or MTProto implementation. */
public final class AuthenticationController implements AutoCloseable {
    public enum State { NEW, INITIALIZING, READY, STARTING, CODE_REQUIRED, VERIFYING,
        LOCAL_AUTHORIZED, COMMITTING, LOCAL_COMPLETE, CANCELLED, FAILED, STORAGE_UNCERTAIN,
        RESTART_REQUIRED, CLOSED }
    public enum Commit { COMMITTED, CONFLICT }
    public interface SessionStore {
        /** Scope/version metadata only. Must not restore/activate or return credentials. */
        StoreSnapshot inspect(SessionScope scope);
        /** Atomic CAS, no overwrite. Synchronous; owns no reference to material after returning.
         * A thrown exception means UNKNOWN commit outcome, not guaranteed rollback. */
        Commit commitLocalIfEmpty(SessionScope scope, long expectedVersion, char[] material);
    }
    public static final class StoreSnapshot {
        public final SessionScope scope;
        public final long version;
        public final boolean present;
        public StoreSnapshot(SessionScope scope, long version, boolean present) {
            if (scope == null || version < 0) throw new IllegalArgumentException("INVALID_STORE_METADATA");
            this.scope=scope; this.version=version; this.present=present;
        }
        @Override public String toString() { return "StoreSnapshot[present=" + present + "]"; }
    }
    /** UI-only, no identity/code/challenge/token/ticket. Never resumes an in-flight login after process death. */
    public static final class UiSnapshot {
        public final SessionScope scope;
        public final State state;
        public final Fault fault;
        public final long revision;
        private UiSnapshot(SessionScope scope, State state, Fault fault, long revision) {
            this.scope=scope; this.state=state; this.fault=fault; this.revision=revision;
        }
        public static UiSnapshot recreationMarker(SessionScope scope) {
            if (scope == null) throw new IllegalArgumentException("SCOPE_REQUIRED");
            return new UiSnapshot(scope,State.RESTART_REQUIRED,Fault.NONE,0);
        }
        @Override public String toString() { return "AuthUi[" + state + "," + fault + "]"; }
    }
    private final SessionScope scope;
    private final ClosedRuntime runtime;
    private final RequestCoordinator broker;
    private final SessionStore store;
    private final AuthUiRelay ui;
    private State state=State.NEW;
    private Fault fault=Fault.NONE;
    private long generation, storeVersion, revision;
    private char[] challenge, stagedSession;
    public AuthenticationController(ClosedRuntime runtime, TransportPort transport, SessionStore store) {
        if (runtime == null || store == null) throw new IllegalArgumentException("AUTH_DEPENDENCIES_REQUIRED");
        this.runtime=runtime; this.scope=runtime.scope; this.store=store; this.broker=new RequestCoordinator(runtime,transport);
        this.ui=new AuthUiRelay(snapshot());
    }
    public AuthUiRelay.Binding observe(java.util.concurrent.Executor executor, AuthUiRelay.Observer observer) {
        return ui.attach(executor,observer);
    }
    public int uiObserverFailures() { return ui.observerFailures(); }
    public int uiExecutorFailures() { return ui.executorFailures(); }
    public int adapterFailures() { return broker.adapterFailures(); }
    public synchronized UiSnapshot snapshot() { return new UiSnapshot(scope,state,fault,revision); }
    public boolean initialize() {
        long epoch;
        synchronized(this) {
            if (state == State.READY) return true;
            if (state != State.NEW) return false;
            transition(State.INITIALIZING,Fault.NONE); epoch=++generation;
        }
        ui.publish(snapshot());
        Fault failure=Fault.NONE;
        StoreSnapshot metadata=null;
        try {
            metadata=store.inspect(scope);
            failure=validate(metadata);
            if (failure == Fault.NONE) {
                synchronized(this) { if (generation != epoch || state != State.INITIALIZING) return false; }
                if (!broker.initialize()) failure=Fault.INITIALIZATION;
                else { metadata=store.inspect(scope); failure=validate(metadata); }
            }
        } catch (RuntimeException | LinkageError unavailable) { failure=Fault.STORAGE; }
        boolean ready;
        synchronized(this) {
            if (generation != epoch || state != State.INITIALIZING) return false;
            ready=failure == Fault.NONE;
            if (ready) { transition(State.READY,Fault.NONE); storeVersion=metadata.version; }
            else fail(failure);
        }
        if (!ready) broker.close();
        ui.publish(snapshot());
        return ready;
    }
    private Fault validate(StoreSnapshot metadata) {
        if (metadata == null || !scope.equals(metadata.scope)) return Fault.INVALID_SCOPE;
        return metadata.present ? Fault.EXISTING_SESSION : Fault.NONE;
    }
    public boolean start(char[] localIdentity) { return request(false,localIdentity); }
    public boolean submitCode(char[] localCode) { return request(true,localCode); }
    private boolean request(boolean verification, char[] supplied) {
        final long epoch;
        final Input input;
        synchronized(this) {
            if (supplied == null || supplied.length == 0 || supplied.length > 256
                    || state != (verification ? State.CODE_REQUIRED : State.READY)) return false;
            input=new Input(supplied,verification ? challenge : new char[0]);
            transition(verification ? State.VERIFYING : State.STARTING,Fault.NONE);
            epoch=++generation;
        }
        ui.publish(snapshot());
        broker.submit(scope,verification ? Operation.VERIFY_CODE : Operation.REQUEST_CODE,
                input,reply -> receive(epoch,verification,reply));
        return true;
    }
    private synchronized void receive(long epoch, boolean verification, Reply reply) {
        if (epoch != generation || state != (verification ? State.VERIFYING : State.STARTING)) return;
        if (reply.kind != (verification ? Kind.LOCAL_SESSION : Kind.CODE_SENT) || reply.fault != Fault.NONE) {
            fail(reply.fault == Fault.NONE ? Fault.PROTOCOL : reply.fault); broker.close(); return;
        }
        char[] material;
        try { material=reply.materialCopy(); }
        catch (RuntimeException unavailable) { fail(Fault.PROTOCOL); broker.close(); return; }
        if (material.length == 0) { wipe(material); fail(Fault.PROTOCOL); broker.close(); return; }
        if (verification) { wipe(challenge); challenge=null; stagedSession=material; transition(State.LOCAL_AUTHORIZED,Fault.NONE); broker.close(); }
        else { challenge=material; transition(State.CODE_REQUIRED,Fault.NONE); }
        ui.publish(snapshot());
    }
    /** Explicit local commit, not onAuthSuccess and not UserConfig.setCurrentUser. Never logs out. */
    public synchronized boolean commitLocal() {
        if (state != State.LOCAL_AUTHORIZED) return false;
        transition(State.COMMITTING,Fault.NONE);
        ui.publish(snapshot());
        char[] copy=stagedSession.clone();
        try {
            Commit result=store.commitLocalIfEmpty(scope,storeVersion,copy);
            if (result == Commit.COMMITTED) { transition(State.LOCAL_COMPLETE,Fault.NONE); ui.publish(snapshot()); return true; }
            if (result == Commit.CONFLICT) { fail(Fault.CONFLICT); return false; }
            transition(State.STORAGE_UNCERTAIN,Fault.STORAGE_UNCERTAIN); ui.publish(snapshot()); return false;
        } catch (RuntimeException | LinkageError unavailable) {
            transition(State.STORAGE_UNCERTAIN,Fault.STORAGE_UNCERTAIN); ui.publish(snapshot()); return false;
        } finally { wipe(copy); clearMaterial(); }
    }
    public boolean cancel() {
        synchronized(this) {
            if (state == State.CLOSED || state == State.CANCELLED || state == State.COMMITTING
                    || state == State.LOCAL_COMPLETE || state == State.STORAGE_UNCERTAIN) return false;
            ++generation; transition(State.CANCELLED,Fault.CANCELLED); clearMaterial();
        }
        // Local flow ownership only. No global cleanup, cancel-code RPC, logout or key reset.
        broker.close(); ui.publish(snapshot()); return true;
    }
    public synchronized boolean restoreUi(UiSnapshot previous) {
        if (state != State.NEW || previous == null || !scope.equals(previous.scope)) return false;
        transition(State.RESTART_REQUIRED,Fault.NONE); ui.publish(snapshot()); return true;
    }
    public ClosedRuntime.Decision requestDestructiveOperation(ClosedRuntime.Operation operation) {
        if (operation == null) throw new IllegalArgumentException("OPERATION_REQUIRED");
        return runtime.authorize(operation);
    }
    private void transition(State next, Fault reason) { state=next; fault=reason; revision++; }
    private void fail(Fault reason) { transition(State.FAILED,reason); clearMaterial(); ui.publish(snapshot()); }
    private void clearMaterial() { wipe(challenge); wipe(stagedSession); challenge=stagedSession=null; }
    private static void wipe(char[] material) { if (material != null) Arrays.fill(material,'\0'); }
    public void close() {
        synchronized(this) {
            if (state == State.CLOSED) return;
            // A same-thread reentrant close from a storage adapter is deferred to the caller.
            if (state == State.COMMITTING) return;
            ++generation; transition(State.CLOSED,fault); clearMaterial();
        }
        broker.close(); ui.close();
    }
}
