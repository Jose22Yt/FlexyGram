package org.telegram.ui.realalpha;

import android.content.Intent;
import android.os.Bundle;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.AccountInstance;
import org.telegram.messenger.NativeLoader;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.LaunchActivity;
import org.telegram.ui.DialogsActivity;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.INavigationLayout;

/** Real LaunchActivity + DialogsActivity. No preview cells, fake account or replacement chat UI. */
public final class RealAlphaActivity extends LaunchActivity {
    private static final RealAlphaBootstrap BOOTSTRAP = new RealAlphaBootstrap();
    private final RealAlphaBack back = new RealAlphaBack(this, this::onBackPressed);

    private static final RealAlphaBootstrap.Accounts ACCOUNTS = new RealAlphaBootstrap.Accounts() {
        @Override public void initialize() {
            ApplicationLoader.postInitApplication();
            if (!NativeLoader.loaded()) {
                throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_NATIVE_NOT_LOADED");
            }
            AccountInstance account = AccountInstance.getInstance(UserConfig.selectedAccount);
            // Reuse the real, app-private controllers. UserConfig stays empty; transport stays denied.
            if (account.getMessagesController() == null || account.getMessagesStorage() == null
                    || account.getConnectionsManager() == null) {
                throw new IllegalStateException("FLEXYGRAM_REAL_ALPHA_CONTROLLERS_UNAVAILABLE");
            }
        }
        @Override public int count() { return UserConfig.MAX_ACCOUNT_COUNT; }
        @Override public int selected() { return UserConfig.selectedAccount; }
        @Override public boolean containsIdentity(int account) {
            UserConfig config = UserConfig.getInstance(account);
            return config.isClientActivated() || config.getCurrentUser() != null
                    || config.getClientUserId() != 0 || config.clientUserId != 0;
        }
    };

    @Override protected void onCreate(Bundle state) {
        BOOTSTRAP.ensure(ACCOUNTS);
        // No deep links, share/login extras, or restoration of an unreviewed account-bound screen.
        setIntent(new Intent(this, RealAlphaActivity.class).setAction(Intent.ACTION_MAIN));
        super.onCreate(null);
        back.register();
    }

    @Override protected BaseFragment getClientNotActivatedFragment() {
        return new DialogsActivity(null);
    }

    @Override public boolean needPresentFragment(INavigationLayout layout,
            INavigationLayout.NavigationParams params) {
        return permitted(params.fragment) && super.needPresentFragment(layout, params);
    }

    @Override public boolean needAddFragmentToStack(BaseFragment fragment, INavigationLayout layout) {
        return permitted(fragment) && super.needAddFragmentToStack(fragment, layout);
    }

    private boolean permitted(BaseFragment fragment) {
        RealAlphaPolicy.requireClosedBuild();
        // Native empty dialogs only in P1/P2. Login, Sessions and Chat require later reviewed stages.
        return fragment != null && fragment.getClass() == DialogsActivity.class;
    }

    @Override public void onNewIntent(Intent ignored) {
        // This launcher has no deep-link contract. Do not forward extras to Telegram handlers.
    }

    @Override public void startActivityForResult(Intent intent, int requestCode, Bundle options) {
        // Explicit cancellation, rather than opening browsers, pickers, login apps or remote SDKs.
        if (requestCode >= 0) onActivityResult(requestCode, RESULT_CANCELED, null);
    }

    @Override public void startActivities(Intent[] intents, Bundle options) {
        // No external activity capabilities have been reviewed for P1/P2.
    }

    @Override protected void onDestroy() {
        back.close();
        super.onDestroy();
    }
}
