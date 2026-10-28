/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import org.telegram.tgnet.TLRPC;

/**
 * Mandatory TL document attributes; handing a .webp to photo/document send is wrong.
 * The host MUST send through the real Telegram sticker-media path and verify returned
 * document attributes. This type deliberately does not send to a peer by itself.
 */
public final class NativeStickerMetadata {
    private NativeStickerMetadata() {}
    public static TLRPC.TL_document create(int width, int height, int byteLength, String emoji) {
        if (Math.max(width,height) != BubbleStickerSpec.MAX_SIDE || Math.min(width,height) < 1
                || byteLength < 1 || byteLength > BubbleStickerSpec.MAX_BYTES)
            throw new IllegalArgumentException("Not eligible static sticker");
        TLRPC.TL_document d = new TLRPC.TL_document();
        d.mime_type = BubbleStickerSpec.MIME;
        d.size = byteLength;
        d.file_reference = new byte[0];
        TLRPC.TL_documentAttributeImageSize size = new TLRPC.TL_documentAttributeImageSize();
        size.w = width;
        size.h = height;
        d.attributes.add(size);
        TLRPC.TL_documentAttributeSticker sticker = new TLRPC.TL_documentAttributeSticker();
        sticker.alt = emoji == null || emoji.isEmpty() ? "💬" : emoji;
        sticker.stickerset = new TLRPC.TL_inputStickerSetEmpty();
        d.attributes.add(sticker);
        return d;
    }
    public static boolean isNativeStaticSticker(TLRPC.Document document) {
        if (document == null || !BubbleStickerSpec.MIME.equals(document.mime_type)) return false;
        boolean sticker = false, dimensions = false;
        for (TLRPC.DocumentAttribute attribute : document.attributes) {
            if (attribute instanceof TLRPC.TL_documentAttributeSticker) sticker = true;
            if (attribute instanceof TLRPC.TL_documentAttributeImageSize) {
                TLRPC.TL_documentAttributeImageSize s = (TLRPC.TL_documentAttributeImageSize) attribute;
                dimensions |= s.w > 0 && s.h > 0 && Math.max(s.w,s.h) == BubbleStickerSpec.MAX_SIDE;
            }
        }
        return sticker && dimensions;
    }
}
