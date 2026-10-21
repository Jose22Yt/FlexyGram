package org.telegram.ui.realalpha.diagnostics;

import android.app.*;
import android.content.Context;
import android.os.*;
import android.view.ViewTreeObserver;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.StartupTrace;
import static org.telegram.messenger.StartupTrace.Stage.*;

/** Reporter skips Telegram initialization; only the separate probe process runs the real loader. */
public final class StartupDiagnosticApplication extends ApplicationLoader {
    private boolean probe;
    @Override protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        if (!StartupTrace.enabled()) throw new IllegalStateException("STARTUP_DIAGNOSTIC_IDENTITY_REQUIRED");
        StartupTrace.attach(this);
        String expected = getPackageName() + ":startup_probe";
        if (Build.VERSION.SDK_INT >= 28) {
            probe = expected.equals(Application.getProcessName());
        } else {
            ActivityManager manager = (ActivityManager)getSystemService(ACTIVITY_SERVICE);
            if (manager != null && manager.getRunningAppProcesses() != null) {
                for (ActivityManager.RunningAppProcessInfo info : manager.getRunningAppProcesses()) {
                    if (info.pid == android.os.Process.myPid() && info.uid == android.os.Process.myUid()) {
                        probe = expected.equals(info.processName);
                    }
                }
            }
        }
        if (probe) StartupTrace.begin(APPLICATION_ATTACH);
    }
    @Override public void onCreate() {
        if (!probe) return; // android.app.Application.onCreate is empty. Do NOT initialize Telegram here.
        StartupTrace.stage(APPLICATION_ENTER);
        registerActivityLifecycleCallbacks(new ActivityLifecycleCallbacks() {
            @Override public void onActivityCreated(Activity a, Bundle b) {}
            @Override public void onActivityStarted(Activity a) {}
            @Override public void onActivityResumed(Activity a) {
                StartupTrace.stage(ACTIVITY_RESUMED);
                final android.view.View view = a.getWindow().getDecorView();
                view.getViewTreeObserver().addOnDrawListener(new ViewTreeObserver.OnDrawListener() {
                    private boolean drawn;
                    @Override public void onDraw() {
                        if (drawn) return;
                        drawn = true;
                        StartupTrace.stage(FIRST_DRAW);
                        view.post(() -> {
                            if (view.getViewTreeObserver().isAlive()) view.getViewTreeObserver().removeOnDrawListener(this);
                        });
                    }
                });
            }
            @Override public void onActivityPaused(Activity a) {}
            @Override public void onActivityStopped(Activity a) {}
            @Override public void onActivitySaveInstanceState(Activity a, Bundle b) {}
            @Override public void onActivityDestroyed(Activity a) {
                StartupTrace.stage(a.isFinishing() ? ACTIVITY_FINISHING : ACTIVITY_DESTROYED);
            }
        });
        try {
            super.onCreate();
            StartupTrace.stage(APPLICATION_RETURN);
        } catch (RuntimeException | Error error) {
            StartupTrace.failure(error);
            throw new IllegalStateException("FLEXYGRAM_STARTUP_APPLICATION_FAILED");
        }
    }
}
