package org.telegram.ui.realalpha;

/** Terminal failure on partial initialization. Doubles belong in host tests, not app accounts. */
final class RealAlphaBootstrap {
    interface Accounts {
        void initialize();
        int count();
        int selected();
        boolean containsIdentity(int account);
    }

    private enum State { NEW, INITIALIZING, READY, FAILED }
    private State state = State.NEW;

    synchronized void ensure(Accounts accounts) {
        RealAlphaPolicy.requireClosedBuild();
        if (state == State.FAILED || state == State.INITIALIZING) {
            throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_PARTIAL_INITIALIZATION");
        }
        if (state == State.READY) {
            requireEmpty(accounts);
            return;
        }
        state = State.INITIALIZING;
        try {
            requireEmpty(accounts);
            accounts.initialize();
            requireEmpty(accounts);
            state = State.READY;
        } catch (RuntimeException | Error failure) {
            state = State.FAILED;
            // The cause is deliberately not copied: native/SDK exceptions can contain private data.
            throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_INITIALIZATION_FAILED");
        }
    }

    private void requireEmpty(Accounts accounts) {
        int count = accounts.count();
        int selected = accounts.selected();
        if (count < 1 || selected < 0 || selected >= count) {
            throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_INVALID_ACCOUNT_SLOT");
        }
        for (int slot = 0; slot < count; slot++) {
            if (accounts.containsIdentity(slot)) {
                // Never clear, revoke, import, fabricate or silently reuse an identity.
                throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_ACCOUNT_MUST_BE_EMPTY");
            }
        }
    }
}
