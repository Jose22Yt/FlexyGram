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
    /** Validates RIFF length and recognized VP8/VP8L/VP8X chunk signature, not image decode. */
    public static boolean isWebp(byte[] b) {
        if (b == null || b.length < 20 || b.length > MAX_BYTES
            || b[0]!='R'||b[1]!='I'||b[2]!='F'||b[3]!='F'
            || b[8]!='W'||b[9]!='E'||b[10]!='B'||b[11]!='P'
            || b[12]!='V'||b[13]!='P'||b[14]!='8') return false;
        int marker = b[15] & 0xff;
        if (marker != ' ' && marker != 'L' && marker != 'X') return false;
        long bytes = (b[4]&255L) | ((b[5]&255L)<<8) | ((b[6]&255L)<<16) | ((b[7]&255L)<<24);
        return bytes == b.length-8L;
    }
}
