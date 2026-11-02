/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.stickers;

/**
 * Standard protocol specifications for Telegram native static stickers.
 * Static stickers must be WebP format with maximum side exactly 512px and max size 512KB.
 */
public final class BubbleStickerSpec {
    public static final int MAX_SIDE = 512;
    public static final int MAX_BYTES = 512 * 1024;
    public static final String MIME = "image/webp";

    private BubbleStickerSpec() {}

    /**
     * Calculates scaled sticker dimensions preserving original aspect ratio.
     * Exactly one dimension will be MAX_SIDE (512px), and the other will be <= MAX_SIDE.
     */
    public static int[] dimensions(int width, int height) {
        if (width < 1 || height < 1) {
            throw new IllegalArgumentException("Invalid dimensions");
        }
        if (width >= height) {
            int h = Math.max(1, Math.round((float) MAX_SIDE * height / (float) width));
            return new int[]{MAX_SIDE, Math.min(MAX_SIDE, h)};
        } else {
            int w = Math.max(1, Math.round((float) MAX_SIDE * width / (float) height));
            return new int[]{Math.min(MAX_SIDE, w), MAX_SIDE};
        }
    }

    /**
     * Checks if the byte array starts with a valid WebP container header (RIFF...WEBP).
     */
    public static boolean isWebp(byte[] b) {
        if (b == null || b.length < 20 || b.length > MAX_BYTES
                || b[0] != 'R' || b[1] != 'I' || b[2] != 'F' || b[3] != 'F'
                || b[8] != 'W' || b[9] != 'E' || b[10] != 'B' || b[11] != 'P'
                || b[12] != 'V' || b[13] != 'P' || b[14] != '8') {
            return false;
        }
        int marker = b[15] & 0xff;
        if (marker != ' ' && marker != 'L' && marker != 'X') {
            return false;
        }
        long bytes = (b[4] & 0xffL) | ((b[5] & 0xffL) << 8) | ((b[6] & 0xffL) << 16) | ((b[7] & 0xffL) << 24);
        return bytes == b.length - 8L;
    }
}
