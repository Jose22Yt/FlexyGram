package io.github.jose22yt.flexygram.session;

/** Logical storage/ownership key, never a user id, phone number or filesystem path. */
public final class SessionScope {
    public enum Variant {
        DIAGNOSTIC("diagnostic", "io.github.jose22yt.flexygram.diagnostic"),
        BETA_DEVELOPMENT("betaDevelopment", "io.github.jose22yt.flexygram.beta.development"),
        REAL_ALPHA("realAlpha", "io.github.jose22yt.flexygram.realalpha");
        public final String name;
        public final String applicationId;
        Variant(String name, String applicationId) { this.name = name; this.applicationId = applicationId; }
    }
    // Bound to UserConfig.MAX_ACCOUNT_COUNT by a source contract test. No selectedAccount global.
    public static final int ACCOUNT_LIMIT = 10;
    public final Variant variant;
    public final int account;
    private SessionScope(Variant variant, int account) { this.variant = variant; this.account = account; }
    public static SessionScope of(String variantName, String applicationId, int account) {
        if (account < 0 || account >= ACCOUNT_LIMIT) throw new IllegalArgumentException("INVALID_ACCOUNT_SLOT");
        for (Variant variant : Variant.values()) {
            if (variant.name.equals(variantName) && variant.applicationId.equals(applicationId)) {
                return new SessionScope(variant, account);
            }
        }
        throw new IllegalArgumentException("UNREVIEWED_SESSION_SCOPE");
    }
    public String storageKey() { return variant.applicationId + "/account/" + account; }
    @Override public boolean equals(Object other) {
        return other instanceof SessionScope && ((SessionScope) other).variant == variant
                && ((SessionScope) other).account == account;
    }
    @Override public int hashCode() { return variant.ordinal() * ACCOUNT_LIMIT + account; }
    @Override public String toString() { return "SessionScope[" + variant.name + ",slot=" + account + "]"; }
}
