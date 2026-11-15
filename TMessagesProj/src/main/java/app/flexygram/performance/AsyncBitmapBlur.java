/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.graphics.Bitmap;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.Utilities;
import java.util.concurrent.*;

/** Owns only accepted, unpublished captures. UI owns a successful result after delivery. */
public final class AsyncBitmapBlur {
    public interface Callback { void done(Bitmap bitmap); }
    private static final ThreadPoolExecutor WORKER = new ThreadPoolExecutor(0, 1, 1, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(1), task -> {
                Thread thread = new Thread(() -> {
                    android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND);
                    task.run();
                }, "FlexyReactionBlur");
                thread.setDaemon(true);
                return thread;
            }, new ThreadPoolExecutor.AbortPolicy());
    private AsyncBitmapBlur() { }

    public static boolean submit(Bitmap capture, int radius, Callback callback) {
        try {
            WORKER.execute(() -> {
                Bitmap result = capture;
                android.os.Trace.beginSection("Flexy.reactions.blur.cpu");
                try {
                    Utilities.stackBlurBitmap(capture, radius);
                } catch (RuntimeException | OutOfMemoryError unavailable) {
                    capture.recycle();
                    result = null;
                } finally {
                    android.os.Trace.endSection();
                }
                Bitmap ready = result;
                AndroidUtilities.runOnUIThread(() -> callback.done(ready));
            });
            return true;
        } catch (RejectedExecutionException busy) {
            return false;
        }
    }
}
