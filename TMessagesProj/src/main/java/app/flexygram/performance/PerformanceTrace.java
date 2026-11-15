package app.flexygram.performance;

import android.os.Build;
import android.os.Trace;

import java.util.concurrent.atomic.AtomicInteger;

/** Optional system-trace markers. Does not start a recording or collect message data. */
public final class PerformanceTrace {
    private static final AtomicInteger cookies = new AtomicInteger();

    private PerformanceTrace() {}

    public static int beginAsync(String name) {
        if (Build.VERSION.SDK_INT < 29 || !Trace.isEnabled()) {
            return 0;
        }
        int cookie = cookies.incrementAndGet();
        if (cookie == 0) {
            cookie = cookies.incrementAndGet();
        }
        Trace.beginAsyncSection(name, cookie);
        return cookie;
    }

    public static void endAsync(String name, int cookie) {
        if (cookie != 0 && Build.VERSION.SDK_INT >= 29) {
            Trace.endAsyncSection(name, cookie);
        }
    }
}
