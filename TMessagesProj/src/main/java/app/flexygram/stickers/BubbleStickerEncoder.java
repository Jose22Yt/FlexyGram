/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.stickers;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.PorterDuff;
import android.os.Build;
import android.os.Looper;
import org.telegram.messenger.MessageObject;
import org.telegram.ui.Cells.ChatMessageCell;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * Handles capturing native ChatMessageCell bubble drawing and encoding to Telegram-compliant WebP.
 */
public final class BubbleStickerEncoder {

    public static final class StickerBytes {
        public final byte[] bytes;
        public final int width;
        public final int height;

        public StickerBytes(byte[] bytes, int width, int height) {
            this.bytes = bytes;
            this.width = width;
            this.height = height;
        }
    }

    private BubbleStickerEncoder() {}

    /**
     * Checks if a message bubble is eligible for conversion to sticker.
     */
    public static boolean isEligible(ChatMessageCell cell, MessageObject message) {
        if (cell == null || message == null || message.messageOwner == null
                || message.isSponsored() || cell.getAlpha() < 0.99f
                || cell.getCurrentBackgroundDrawable(false) == null) {
            return false;
        }
        if (message.messageOwner.noforwards || message.isEphemeral() || message.messageOwner.ttl != 0) {
            return false;
        }
        int left = cell.getBackgroundDrawableLeft();
        int right = cell.getBackgroundDrawableRight();
        int top = cell.getBackgroundDrawableTop() + cell.getPaddingTop();
        int bottom = cell.getBackgroundDrawableBottom() + cell.getPaddingTop();
        int w = right - left;
        int h = bottom - top;
        return w > 10 && h > 10;
    }

    /**
     * Captures the bubble view into an ARGB_8888 bitmap with transparent background.
     * Must be called on UI thread.
     */
    public static Bitmap captureBubble(ChatMessageCell cell, MessageObject message) {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("Bubble capture must run on UI thread");
        }
        if (!isEligible(cell, message)) {
            throw new IllegalArgumentException("Bubble not eligible for sticker conversion");
        }

        int left = cell.getBackgroundDrawableLeft();
        int right = cell.getBackgroundDrawableRight();
        int top = cell.getBackgroundDrawableTop() + cell.getPaddingTop();
        int bottom = cell.getBackgroundDrawableBottom() + cell.getPaddingTop();
        int sourceW = Math.max(1, right - left);
        int sourceH = Math.max(1, bottom - top);

        int[] targetDims = BubbleStickerSpec.dimensions(sourceW, sourceH);
        Bitmap bitmap = Bitmap.createBitmap(targetDims[0], targetDims[1], Bitmap.Config.ARGB_8888);

        Canvas canvas = new Canvas(bitmap);
        canvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
        canvas.scale(targetDims[0] / (float) sourceW, targetDims[1] / (float) sourceH);
        canvas.translate(-left, -top);
        canvas.clipRect(left, top, right, bottom);

        if (cell.drawBackgroundInParent()) {
            int bg = canvas.save();
            canvas.translate(0, cell.getPaddingTop());
            cell.drawBackgroundInternal(canvas, true);
            canvas.restoreToCount(bg);
        }

        cell.draw(canvas);

        if (cell.hasOutboundsContent()) {
            int out = canvas.save();
            canvas.translate(0, cell.getPaddingTop());
            cell.drawOutboundsContent(canvas);
            canvas.restoreToCount(out);
        }

        return bitmap;
    }

    /**
     * Compresses the bitmap to standard WebP format. Runs off the main thread.
     */
    public static StickerBytes encodeAndRecycle(Bitmap bitmap) throws IOException {
        if (bitmap == null || bitmap.isRecycled()) {
            throw new IOException("Missing or recycled bitmap");
        }
        try {
            int w = bitmap.getWidth();
            int h = bitmap.getHeight();
            ByteArrayOutputStream out = new ByteArrayOutputStream();

            if (Build.VERSION.SDK_INT >= 30) {
                if (bitmap.compress(Bitmap.CompressFormat.WEBP_LOSSLESS, 100, out)) {
                    byte[] bytes = out.toByteArray();
                    if (bytes.length <= BubbleStickerSpec.MAX_BYTES && BubbleStickerSpec.isWebp(bytes)) {
                        return new StickerBytes(bytes, w, h);
                    }
                }
            }

            Bitmap.CompressFormat fmt = Build.VERSION.SDK_INT >= 30
                    ? Bitmap.CompressFormat.WEBP_LOSSY : Bitmap.CompressFormat.WEBP;
            for (int quality = 95; quality >= 40; quality -= 10) {
                out.reset();
                if (bitmap.compress(fmt, quality, out)) {
                    byte[] bytes = out.toByteArray();
                    if (bytes.length <= BubbleStickerSpec.MAX_BYTES && BubbleStickerSpec.isWebp(bytes)) {
                        return new StickerBytes(bytes, w, h);
                    }
                }
            }

            byte[] finalBytes = out.toByteArray();
            if (BubbleStickerSpec.isWebp(finalBytes)) {
                return new StickerBytes(finalBytes, w, h);
            }
            throw new IOException("Failed to encode valid WebP sticker");
        } finally {
            if (!bitmap.isRecycled()) {
                bitmap.recycle();
            }
        }
    }

    /**
     * Writes the encoded sticker bytes to a temporary file.
     */
    public static File writeToCache(File cacheDir, StickerBytes data) throws IOException {
        if (data == null || !BubbleStickerSpec.isWebp(data.bytes)) {
            throw new IOException("Invalid sticker bytes");
        }
        File file = File.createTempFile("flexy_bubble_sticker_", ".webp", cacheDir);
        boolean ok = false;
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write(data.bytes);
            fos.flush();
            ok = true;
            return file;
        } finally {
            if (!ok && file.exists()) {
                file.delete();
            }
        }
    }
}
