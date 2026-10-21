package io.github.jose22yt.flexygram.session;

/** Read-only build/native coherence check. Attestation is NOT permission to open transport. */
public final class ClosedRuntime {
    public enum Operation { INITIALIZE_MTPROTO, REQUEST_CODE, VERIFY_CODE, RESTORE_SESSION,
        LOGOUT, REVOKE_CURRENT, REVOKE_OTHERS, RESET_ALL_SESSIONS }
    public enum Decision { DENIED }
    public final SessionScope scope;
    private final String policyScope;
    private ClosedRuntime(SessionScope scope, String policyScope) {
        this.scope = scope; this.policyScope = policyScope;
    }
    public static ClosedRuntime verify(SessionScope scope, String policyScope, boolean isolated,
            boolean[] capabilities, int apiId, char[] apiHash, String nativeStatement) {
        if (scope == null || policyScope == null || !isolated || capabilities == null
                || capabilities.length != 6 || apiId != 0 || apiHash == null || apiHash.length != 0
                || !policyScope.matches("[a-f0-9]{64}:" + scope.variant.name)) {
            throw new IllegalArgumentException("CLOSED_BUILD_REQUIRED");
        }
        for (boolean enabled : capabilities) {
            if (enabled) throw new IllegalArgumentException("CLOSED_BUILD_REQUIRED");
        }
        String expected = "FLEXYGRAM_POLICY:" + policyScope
                + ":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0";
        if (!expected.equals(nativeStatement)) throw new IllegalArgumentException("NATIVE_POLICY_MISMATCH");
        // No mutable flags, credential reference, preferences, Intent, plugin or remote config retained.
        return new ClosedRuntime(scope, policyScope);
    }
    public Decision authorize(Operation operation) {
        if (operation == null) throw new IllegalArgumentException("OPERATION_REQUIRED");
        return Decision.DENIED;
    }
    public String policyScope() { return policyScope; }
    @Override public String toString() { return "ClosedRuntime[" + scope.variant.name + "]"; }
}
