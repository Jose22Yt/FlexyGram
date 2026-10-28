/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/** Protocol checks independent of Android image APIs. A WebP file alone is NOT a Telegram sticker. */
public final class BubbleStickerSpec {
    public static final int MAX_SIDE = 512;
    public static final int MAX_BYTES = 512 * 1024;
    public static final String MIME = "image/webp";
    private BubbleStickerSpec() {}
    public static int[] dimensions(int width, int height) {
        if (width < 1 || height < 1 || width > 4096 || height > 4096)
            throw new IllegalArgumentException("Invalid source dimensions");
        if (Math.max(width, height) > Math.min(width, height) * 4L)
            throw new IllegalArgumentException("Message is too long for a legible sticker");
        if (width >= height)
            return new int[]{MAX_SIDE, Math.max(1, Math.round(MAX_SIDE * height / (float) width))};
        return new int[]{Math.max(1, Math.round(MAX_SIDE * width / (float) height)), MAX_SIDE};
    }
    public static boolean isWebp(byte[] bytes) {
        return bytes != null && bytes.length >= 16 && bytes.length <= MAX_BYTES
                && bytes[0]=='R' && bytes[1]=='I' && bytes[2]=='F' && bytes[3]=='F'
                && bytes[8]=='W' && bytes[9]=='E' && bytes[10]=='B' && bytes[11]=='P';
    }
}
