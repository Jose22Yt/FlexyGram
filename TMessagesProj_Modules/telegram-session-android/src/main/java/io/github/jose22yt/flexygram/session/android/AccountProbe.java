package io.github.jose22yt.flexygram.session.android;
import io.github.jose22yt.flexygram.session.SessionScope;

/** Metadata only. EMPTY requires persisted-artifact inspection, not just an empty UserConfig. */
public interface AccountProbe {
    enum Evidence { EMPTY, EXISTING_ACCOUNT, NATIVE_FILES_PRESENT, UNAVAILABLE }
    final class Snapshot {
        public final SessionScope scope;
        public final Evidence evidence;
        public final boolean controllerHandlesAvailable;
        public Snapshot(SessionScope scope, Evidence evidence, boolean handles) {
            if(scope==null || evidence==null) throw new IllegalArgumentException("ACCOUNT_METADATA_REQUIRED");
            this.scope=scope; this.evidence=evidence; this.controllerHandlesAvailable=handles;
        }
        @Override public String toString() { return "AccountMetadata["+evidence+"]"; }
    }
    Snapshot inspect();
}
