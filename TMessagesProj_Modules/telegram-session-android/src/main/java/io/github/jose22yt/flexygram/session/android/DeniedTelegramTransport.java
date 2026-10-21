package io.github.jose22yt.flexygram.session.android;
import io.github.jose22yt.flexygram.session.SessionScope;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;

/** Only supplied Telegram port: also denies direct calls, without touching native state. */
public final class DeniedTelegramTransport implements TransportPort {
    private final SessionScope scope;
    public DeniedTelegramTransport(SessionScope scope){if(scope==null)throw new IllegalArgumentException("SCOPE_REQUIRED");this.scope=scope;}
    public SessionScope scope(){return scope;}
    public Domain domain(){return Domain.TELEGRAM;}
    public void initialize(){throw new IllegalStateException("TELEGRAM_TRANSPORT_NOT_AUTHORIZED");}
    public Cancellation submit(Attempt attempt,Listener listener){throw new IllegalStateException("TELEGRAM_TRANSPORT_NOT_AUTHORIZED");}
    public void close(){/* Never logout, cleanup or revoke. */}
}
