/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.os.Build;
import android.os.Looper;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * Static-sticker encoder. Capture MUST be requested on the UI thread from the already
 * visible, eligible native bubble renderer. Compression can run off-main. Never screenshot
 * the whole conversation, read hidden content or render a protected/TTL message.
 */
public final class BubbleStickerEncoder {
    public interface NativeBubblePainter {
        int width();
        int height();
        void drawOriginalBubble(Canvas canvas);
    }
    public static final class StickerBytes {
        public final byte[] bytes;
        public final int width, height;
        private StickerBytes(byte[] bytes, int width, int height) {
            this.bytes = bytes; this.width = width; this.height = height;
        }
    }
    private BubbleStickerEncoder() {}
    /** Returns an owned bitmap. Caller must recycle it after encoding or cancellation. */
    public static Bitmap captureOnUiThread(NativeBubblePainter painter) {
        if (Looper.myLooper() != Looper.getMainLooper())
            throw new IllegalStateException("Bubble capture must run on UI thread");
        if (painter == null) throw new IllegalArgumentException("painter");
        final int sourceW = painter.width(), sourceH = painter.height();
        int[] size = BubbleStickerSpec.dimensions(sourceW, sourceH);
        Bitmap bitmap = Bitmap.createBitmap(size[0], size[1], Bitmap.Config.ARGB_8888);
        boolean okay = false;
        try {
            Canvas c = new Canvas(bitmap);
            c.drawColor(Color.TRANSPARENT, android.graphics.PorterDuff.Mode.CLEAR);
            c.scale(size[0] / (float) sourceW, size[1] / (float) sourceH);
            painter.drawOriginalBubble(c); // EXACT existing paint implementation provided by host
            okay = true;
            return bitmap;
        } finally {
            if (!okay) bitmap.recycle();
        }
    }
    /** Compression is CPU-heavy. Call off the main thread and release the input bitmap. */
    public static StickerBytes encodeAndRecycle(Bitmap bitmap) throws IOException {
        if (bitmap == null || bitmap.isRecycled()) throw new IOException("Missing bitmap");
        try {
            final int w = bitmap.getWidth(), h = bitmap.getHeight();
            if (Math.max(w,h) != BubbleStickerSpec.MAX_SIDE)
                throw new IOException("Not a Telegram sticker size");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            // Lossless first, then controlled lossy fallback while preserving transparency.
            if (Build.VERSION.SDK_INT >= 30) {
                if (bitmap.compress(Bitmap.CompressFormat.WEBP_LOSSLESS, 100, out)
                        && BubbleStickerSpec.isWebp(out.toByteArray()))
                    return new StickerBytes(out.toByteArray(), w, h);
            }
            Bitmap.CompressFormat fmt = Build.VERSION.SDK_INT >= 30
                    ? Bitmap.CompressFormat.WEBP_LOSSY : Bitmap.CompressFormat.WEBP;
            for (int quality = 95; quality >= 35; quality -= 10) {
                out.reset();
                if (bitmap.compress(fmt, quality, out)
                        && BubbleStickerSpec.isWebp(out.toByteArray()))
                    return new StickerBytes(out.toByteArray(), w, h);
            }
            throw new IOException("Sticker could not meet WebP size limit");
        } finally {
            bitmap.recycle();
        }
    }
    /** Temporary private cache file: delete after native Telegram upload/cancel. */
    public static File writePrivateCache(File cacheDir, StickerBytes data) throws IOException {
        if (data == null || !BubbleStickerSpec.isWebp(data.bytes)
                || Math.max(data.width, data.height) != BubbleStickerSpec.MAX_SIDE)
            throw new IOException("Invalid sticker bytes");
        File file = File.createTempFile("flexy_bubble_sticker_", ".webp", cacheDir);
        boolean okay = false;
        try (FileOutputStream f = new FileOutputStream(file)) {
            f.write(data.bytes);
            f.flush();
            okay = true;
            return file;
        } finally { if (!okay) file.delete(); }
    }
}
