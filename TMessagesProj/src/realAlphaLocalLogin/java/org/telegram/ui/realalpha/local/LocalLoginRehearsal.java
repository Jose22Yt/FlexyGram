package org.telegram.ui.realalpha.local;

import java.util.EnumMap;
import java.util.concurrent.Executor;
import org.telegram.tgnet.TLObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.tgnet.tl.TL_account;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.session.android.*;
import io.github.jose22yt.flexygram.login.*;
import io.github.jose22yt.flexygram.login.NativePersistenceFence.*;
import io.github.jose22yt.flexygram.login.local.LocalLoginSession;

/** In-memory rehearsal only. No account writer, sockets, key format, real proof or credentials. */
public final class LocalLoginRehearsal implements AutoCloseable {
    public enum Scenario { SMS, APP, TWO_FACTOR, REGISTER }
    public final LocalLoginSession pages;
    public final LoginFlowOwner owner;
    private final TelegramRequestContext context;
    private boolean closed;

    public LocalLoginRehearsal(ClosedRuntime runtime, Scenario scenario, Executor serial,
                              NativeLoginProtocol.Clock clock) {
        if (runtime == null || runtime.scope.variant != SessionScope.Variant.REAL_ALPHA
                || scenario == null || serial == null || clock == null)
            throw new IllegalArgumentException("CLOSED_LOCAL_REHEARSAL_REQUIRED");
        SessionScope scope = runtime.scope;
        // This journal and inventory model are NOT Telegram's persisted account/storage.
        OperationJournal.Backend memory = new OperationJournal.Backend() {
            private OperationJournal.Record row = OperationJournal.Record.empty(scope);
            public synchronized OperationJournal.Record read(SessionScope requested) {
                if (!scope.equals(requested)) throw new IllegalArgumentException("LOCAL_SCOPE_REJECTED");
                return row;
            }
            public synchronized boolean compareAndSet(OperationJournal.Record before, OperationJournal.Record after) {
                if (!scope.equals(after.scope) || !row.equals(before)) return false;
                row = after; return true;
            }
        };
        TelegramAuthorizationStore.OriginalFormatPort model = new TelegramAuthorizationStore.OriginalFormatPort() {
            public Domain domain() { return Domain.LOCAL_SIMULATION; }
            public Inventory capture(SessionScope requested) {
                if (!scope.equals(requested)) throw new IllegalArgumentException("LOCAL_SCOPE_REJECTED");
                EnumMap<Artifact, Stamp> values = new EnumMap<>(Artifact.class);
                for (Artifact artifact : Artifact.values()) values.put(artifact, Stamp.absent());
                return new Inventory(scope, false, values);
            }
            public Report commitOriginal(Lease lease, TLRPC.TL_auth_authorization original, NativeLoginProtocol.Action source) {
                throw new IllegalStateException("PERSISTENCE_DISABLED_IN_VISUAL_REHEARSAL");
            }
        };
        TelegramAuthorizationStore store = new TelegramAuthorizationStore(runtime, new OperationJournal(memory, scope), model);
        Script script = new Script(scope, scenario);
        context = new TelegramRequestContext(runtime, store, script, new TelegramRequestContext.LocalProof() {
            public Domain domain() { return Domain.LOCAL_SIMULATION; }
            public TLRPC.TL_inputCheckPasswordSRP create(char[] synthetic, TL_account.Password parameters) {
                // Deliberately non-cryptographic local fixture; never passed to a remote transport.
                TLRPC.TL_inputCheckPasswordSRP proof = new TLRPC.TL_inputCheckPasswordSRP();
                proof.srp_id = parameters.srp_id; proof.A = new byte[]{1}; proof.M1 = new byte[]{2}; return proof;
            }
        });
        NativeLoginTransport transport = store.localTransport(runtime, context, clock);
        owner = new LoginFlowOwner(runtime, transport, store, serial);
        transport.bindLocalStateSignal(owner::signalLocalAdapterState);
        pages = new LocalLoginSession(runtime, owner, transport, context, serial);
    }
    public boolean initialize() { return owner.initializeLocal(false); }
    @Override public synchronized void close() {
        if (closed) return; closed = true; pages.close(); context.close();
    }

    /** Finite local responses. Unsupported/late/out-of-order requests cannot select another provider. */
    private static final class Script implements TelegramRequestContext.LocalPort {
        private final SessionScope scope; private final Scenario scenario;
        private int stage; private boolean closed;
        Script(SessionScope scope, Scenario scenario) { this.scope=scope; this.scenario=scenario; }
        public Domain domain() { return Domain.LOCAL_SIMULATION; }
        public SessionScope scope() { return scope; }
        public synchronized Cancellation submit(TLObject request, int dc, TelegramRequestContext.RawCallback callback) {
            if (closed || dc != 0 || callback == null) throw new IllegalStateException("LOCAL_REQUEST_REJECTED");
            TLObject result = null; TLRPC.TL_error error = null;
            if (stage == 0 && request instanceof TLRPC.TL_auth_sendCode) {
                TLRPC.TL_auth_sendCode send = (TLRPC.TL_auth_sendCode) request;
                if (send.api_id != 0 || !"".equals(send.api_hash)) throw new IllegalStateException("LOCAL_CREDENTIALS_REJECTED");
                TLRPC.TL_auth_sentCode code = new TLRPC.TL_auth_sentCode();
                code.phone_code_hash = "LOCAL_REHEARSAL_NOT_A_TELEGRAM_HASH";
                code.type = scenario == Scenario.APP ? new TLRPC.TL_auth_sentCodeTypeApp() : new TLRPC.TL_auth_sentCodeTypeSms();
                code.type.length = 6; result = code; stage = 1;
            } else if (stage == 1 && request instanceof TLRPC.TL_auth_signIn) {
                if (!"000000".equals(((TLRPC.TL_auth_signIn) request).phone_code)) error = error("PHONE_CODE_INVALID");
                else if (scenario == Scenario.TWO_FACTOR) { error=error("SESSION_PASSWORD_NEEDED"); stage=2; }
                else if (scenario == Scenario.REGISTER) { result=new TLRPC.TL_auth_authorizationSignUpRequired(); stage=4; }
                else { result=authorization(); stage=5; }
            } else if (stage == 2 && request instanceof TL_account.getPassword) {
                TL_account.TL_password password = new TL_account.TL_password(); password.has_password=true;
                TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow algorithm = new TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow();
                algorithm.salt1=new byte[]{1}; algorithm.salt2=new byte[]{2}; algorithm.p=new byte[]{3}; algorithm.g=2;
                password.current_algo=algorithm; password.srp_B=new byte[]{4}; password.srp_id=1; result=password; stage=3;
            } else if (stage == 3 && request instanceof TLRPC.TL_auth_checkPassword) { result=authorization(); stage=5; }
            else if (stage == 4 && request instanceof TLRPC.TL_auth_signUp) { result=authorization(); stage=5; }
            else error=error("LOCAL_SCENARIO_STATE_REJECTED");
            callback.complete(result, error);
            return () -> {}; // Completed synchronously; no timer, future, network or observer exists.
        }
        private static TLRPC.TL_error error(String type) { TLRPC.TL_error e=new TLRPC.TL_error(); e.code=400; e.text=type; return e; }
        private static TLRPC.TL_auth_authorization authorization() {
            TLRPC.TL_auth_authorization a=new TLRPC.TL_auth_authorization(); a.user=new TLRPC.TL_user(); a.user.id=1; return a;
        }
        public synchronized void close() { closed=true; }
    }
}
