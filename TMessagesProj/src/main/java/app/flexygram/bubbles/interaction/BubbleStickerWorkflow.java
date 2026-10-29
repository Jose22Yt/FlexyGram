/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Handler;
import android.os.Looper;
import org.telegram.tgnet.TLRPC;
import java.io.File;
import java.io.IOException;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * One conversion owner per contextual menu. Captures the *approved* existing bubble
 * on UI; compresses on an idle-releasing bounded worker; never uploads automatically.
 * The host owns permission checks, exact peer/thread/account and the real sticker sender.
 */
public final class BubbleStickerWorkflow {
    public interface Listener {
        void onReady(File webp, Bitmap preview, TLRPC.Document stickerMetadata);
        void onError(String reason);
        void onSent();
    }
    public interface NativeStickerSender {
        /** Must invoke callback after the actual Telegram sticker upload/send finishes. */
        void send(File file, TLRPC.Document sticker, SendResult result);
    }
    public interface SendResult { void complete(TLRPC.Document serverDocument, Throwable error); }

    private static final ThreadPoolExecutor WORKER = new ThreadPoolExecutor(0, 1, 30L,
            TimeUnit.SECONDS, new ArrayBlockingQueue<>(2), r -> {
                Thread t = new Thread(r, "FlexyBubbleSticker");
                t.setDaemon(true);
                return t;
            }, new ThreadPoolExecutor.AbortPolicy());
    static { WORKER.allowCoreThreadTimeOut(true); }
    private final Handler main = new Handler(Looper.getMainLooper());
    private final AtomicInteger generation = new AtomicInteger();
    private final File cacheDirectory;
    private File readyFile;
    private TLRPC.Document readyDocument;
    private boolean sending, submitted, preparing;
    private Listener currentListener;
    public boolean isPreparing() { onMain(); return preparing; }
    public File exportFile() { onMain(); return readyFile; }
    public boolean canSend() { onMain(); return readyFile != null && !submitted; }
    public BubbleStickerWorkflow(File cacheDirectory) {
        if (cacheDirectory == null || !cacheDirectory.isDirectory())
            throw new IllegalArgumentException("private cache directory");
        this.cacheDirectory = cacheDirectory;
    }
    private static void onMain() {
        if (Looper.myLooper() != Looper.getMainLooper()) throw new IllegalStateException("UI thread only");
    }
    public void prepare(BubbleStickerEncoder.NativeBubblePainter painter, Listener listener) {
        onMain();
        if (listener == null) throw new IllegalArgumentException("listener");
        cancel();
        currentListener = listener;
        preparing = true;
        int ticket = generation.incrementAndGet();
        final Bitmap bitmap;
        try { bitmap = BubbleStickerEncoder.captureOnUiThread(painter); }
        catch (Exception | OutOfMemoryError e) { preparing = false; listener.onError("capture"); return; }
        try {
            WORKER.execute(() -> {
                File file = null;
                Bitmap preview = null;
                try {
                    BubbleStickerEncoder.StickerBytes encoded = BubbleStickerEncoder.encodeAndRecycle(bitmap);
                    if (ticket != generation.get()) return;
                    file = BubbleStickerEncoder.writePrivateCache(cacheDirectory, encoded);
                    preview = BitmapFactory.decodeByteArray(encoded.bytes, 0, encoded.bytes.length);
                    if (preview == null) throw new IOException("Cannot preview sticker");
                    TLRPC.Document metadata = NativeStickerMetadata.create(
                            encoded.width, encoded.height, encoded.bytes.length, "💬");
                    final File completedFile = file;
                    final Bitmap completedPreview = preview;
                    final TLRPC.Document completedMetadata = metadata;
                    file = null;
                    preview = null;
                    main.post(() -> {
                        if (ticket != generation.get()) {
                            completedFile.delete();
                            completedPreview.recycle();
                            return;
                        }
                        preparing = false;
                        readyFile = completedFile;
                        readyDocument = completedMetadata;
                        listener.onReady(completedFile, completedPreview, completedMetadata);
                        // Listener owns preview until menu closes; recycle on its teardown.
                    });
                } catch (Throwable failure) {
                    if (!bitmap.isRecycled()) bitmap.recycle();
                    if (ticket == generation.get()) main.post(() -> {
                        if (ticket == generation.get()) { preparing = false; listener.onError("encode"); }
                    });
                } finally {
                    if (file != null) file.delete();
                    if (preview != null) preview.recycle();
                }
            });
        } catch (RuntimeException rejected) {
            bitmap.recycle();
            preparing = false;
            listener.onError("busy");
        }
    }
    /** A separate explicit SEND HERE click must call this; not called from prepare(). */
    public void confirmAndSend(NativeStickerSender sender, Listener listener) {
        onMain();
        if (sender == null || listener == null || readyFile == null || readyDocument == null || sending || submitted) return;
        final int ticket = generation.get();
        final File file = readyFile;
        if (!file.isFile() || !NativeStickerMetadata.isNativeStaticSticker(readyDocument)) {
            listener.onError("invalid");
            return;
        }
        sending = submitted = true;
        // An upload owns the file once submitted. Never delete it on menu teardown:
        // Telegram may still upload it or offer its original retry action.
        java.lang.ref.WeakReference<BubbleStickerWorkflow> weak = new java.lang.ref.WeakReference<>(this);
        try {
            sender.send(file, readyDocument, (serverDocument, failure) -> new Handler(Looper.getMainLooper()).post(() -> {
                BubbleStickerWorkflow owner = weak.get();
                if (owner == null || ticket != owner.generation.get() || !owner.sending) return;
                owner.sending = false;
                Listener live = owner.currentListener;
                if (live == null) return;
                if (failure == null && serverDocument != null && serverDocument.id != 0
                        && NativeStickerMetadata.isNativeStaticSticker(serverDocument)) {
                    live.onSent();
                } else live.onError("unconfirmed");
            }));
        } catch (RuntimeException failure) {
            sending = false;
            listener.onError("send");
        }
    }
    /** Cancel is safe for old encoders; transport must independently own a pending upload. */
    public void cancel() {
        onMain();
        generation.incrementAndGet();
        if (!submitted && readyFile != null) readyFile.delete();
        readyFile = null;
        readyDocument = null;
        currentListener = null;
        preparing = sending = submitted = false;
    }
}
