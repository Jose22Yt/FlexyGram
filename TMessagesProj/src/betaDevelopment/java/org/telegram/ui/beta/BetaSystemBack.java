package org.telegram.ui.beta;

import android.app.Activity;
import android.os.Build;

/** Beta-only platform bridge. The existing navigation queue remains the only route executor. */
final class BetaSystemBack implements AutoCloseable {
    private final Activity owner;
    private final Runnable dispatch;
    private Object registration;
    private boolean closed;

    BetaSystemBack(Activity owner, Runnable dispatch) {
        this.owner = owner;
        this.dispatch = dispatch;
    }

    void register() {
        if (closed || registration != null || Build.VERSION.SDK_INT < 33) return;
        registration = Api33.register(owner, () -> {
            if (!closed) dispatch.run();
        });
    }

    @Override public void close() {
        closed = true;
        Object previous = registration;
        registration = null;
        if (previous != null && Build.VERSION.SDK_INT >= 33) Api33.unregister(owner, previous);
    }

    // Keep API33 window types out of the outer class fields/signatures for minSdk24.
    @android.annotation.TargetApi(33)
    private static final class Api33 {
        static Object register(Activity owner, Runnable dispatch) {
            android.window.OnBackInvokedCallback callback = dispatch::run;
            owner.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, callback);
            return callback;
        }

        static void unregister(Activity owner, Object callback) {
            owner.getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(
                    (android.window.OnBackInvokedCallback) callback);
        }
    }
}
