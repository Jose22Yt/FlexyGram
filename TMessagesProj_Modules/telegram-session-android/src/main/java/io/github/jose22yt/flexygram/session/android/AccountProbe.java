package io.github.jose22yt.flexygram.session.android;
import io.github.jose22yt.flexygram.session.SessionScope;

/** Metadata only. EMPTY requires persisted-artifact inspection, not just an empty UserConfig. */
public interface AccountProbe {
    enum Evidence { EMPTY, EXISTING_ACCOUNT, NATIVE_FILES_PRESENT, UNAVAILABLE }
    // Closed enums only: never include exception text, paths, account IDs or preference values.
    enum Diagnostic { EMPTY, EXISTING_ACCOUNT, AUTH_FILES_PRESENT, PROTECTED_AUTH_MATERIAL,
        INSPECTION_UNAVAILABLE, CONTROLLERS_UNAVAILABLE, INITIALIZATION_FAILED,
        ACCESS_DENIED, IO_UNAVAILABLE, INTERNAL_EXCEPTION }
    enum Step { CONTEXT, POLICY, ACCOUNT_HANDLE, USER_CONFIG, PRIVATE_ROOT,
        ACCOUNT_DIRECTORY, AUTH_FILES, STORAGE_HANDLE, CONNECTION_HANDLE, COMPLETE }
    final class Snapshot {
        public final SessionScope scope;
        public final Evidence evidence;
        public final boolean controllerHandlesAvailable;
        public final Diagnostic diagnostic;
        public final Step step;
        public Snapshot(SessionScope scope, Evidence evidence, boolean handles) {
            this(scope,evidence,handles,evidence==Evidence.EMPTY?Diagnostic.EMPTY:
                evidence==Evidence.EXISTING_ACCOUNT?Diagnostic.EXISTING_ACCOUNT:
                evidence==Evidence.NATIVE_FILES_PRESENT?Diagnostic.AUTH_FILES_PRESENT:
                Diagnostic.INSPECTION_UNAVAILABLE,Step.COMPLETE);
        }
        public Snapshot(SessionScope scope, Evidence evidence, boolean handles, Diagnostic diagnostic, Step step) {
            if(scope==null || evidence==null || diagnostic==null || step==null) throw new IllegalArgumentException("ACCOUNT_METADATA_REQUIRED");
            this.scope=scope; this.evidence=evidence; this.controllerHandlesAvailable=handles;
            this.diagnostic=diagnostic; this.step=step;
        }
        @Override public String toString() { return "AccountMetadata["+evidence+"]"; }
    }
    Snapshot inspect();
}
