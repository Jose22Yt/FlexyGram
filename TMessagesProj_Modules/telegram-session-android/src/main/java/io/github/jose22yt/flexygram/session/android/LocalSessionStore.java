package io.github.jose22yt.flexygram.session.android;
import io.github.jose22yt.flexygram.session.AuthenticationController;

/** Shared LOCAL lifecycle. Does not authorize a native write or define an MTProto key format. */
public interface LocalSessionStore extends AuthenticationController.SessionStore, AutoCloseable {
    void beginExplicit(boolean retryApproved);
    @Override void close();
}
