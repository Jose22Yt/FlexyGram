package app.flexygram.icons;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import org.telegram.ui.LauncherIconController;

/** Reconcile persisted alternative aliases immediately after this package is updated. */
public final class SignatureLauncherUpdateReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction()))
            LauncherIconController.tryFixLauncherIconIfNeeded();
    }
}
