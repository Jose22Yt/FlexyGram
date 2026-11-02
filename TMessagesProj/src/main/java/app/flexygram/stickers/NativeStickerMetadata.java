/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.stickers;

import org.telegram.tgnet.TLRPC;

/**
 * Creates and verifies standard Telegram TL document attributes for static stickers.
 * A WebP image sent without TL_documentAttributeSticker is treated as a generic document or photo,
 * NOT a native floating sticker.
 */
public final class NativeStickerMetadata {
    private NativeStickerMetadata() {}

    public static TLRPC.TL_document create(int width, int height, int byteLength, String emoji) {
        if (Math.max(width, height) != BubbleStickerSpec.MAX_SIDE || Math.min(width, height) < 1
                || byteLength < 1 || byteLength > BubbleStickerSpec.MAX_BYTES) {
            throw new IllegalArgumentException("Not an eligible static sticker");
        }
        TLRPC.TL_document d = new TLRPC.TL_document();
        d.mime_type = BubbleStickerSpec.MIME;
        d.size = byteLength;
        d.file_reference = new byte[0];

        TLRPC.TL_documentAttributeImageSize size = new TLRPC.TL_documentAttributeImageSize();
        size.w = width;
        size.h = height;
        d.attributes.add(size);

        TLRPC.TL_documentAttributeSticker sticker = new TLRPC.TL_documentAttributeSticker();
        sticker.alt = (emoji == null || emoji.isEmpty()) ? "💬" : emoji;
        sticker.stickerset = new TLRPC.TL_inputStickerSetEmpty();
        d.attributes.add(sticker);

        return d;
    }

    public static boolean isNativeStaticSticker(TLRPC.Document document) {
        if (document == null || !BubbleStickerSpec.MIME.equals(document.mime_type)
                || document.size < 1 || document.size > BubbleStickerSpec.MAX_BYTES) {
            return false;
        }
        boolean hasSticker = false;
        boolean hasDimensions = false;
        for (TLRPC.DocumentAttribute attribute : document.attributes) {
            if (attribute instanceof TLRPC.TL_documentAttributeSticker) {
                hasSticker = true;
            }
            if (attribute instanceof TLRPC.TL_documentAttributeImageSize) {
                TLRPC.TL_documentAttributeImageSize s = (TLRPC.TL_documentAttributeImageSize) attribute;
                if (s.w > 0 && s.h > 0 && Math.max(s.w, s.h) == BubbleStickerSpec.MAX_SIDE) {
                    hasDimensions = true;
                }
            }
        }
        return hasSticker && hasDimensions;
    }
}
