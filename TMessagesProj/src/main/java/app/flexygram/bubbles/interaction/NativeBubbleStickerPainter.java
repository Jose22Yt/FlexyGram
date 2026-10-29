/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.graphics.Canvas;
import android.graphics.Rect;
import org.telegram.messenger.MessageObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.Cells.ChatMessageCell;

/** One bounded, visible TEXT bubble through its actual native cell painter. No chat screenshot. */
public final class NativeBubbleStickerPainter implements BubbleStickerEncoder.NativeBubblePainter {
    private final ChatMessageCell cell;
    private final MessageObject message;
    private final Rect bounds;
    public static boolean eligible(ChatMessageCell cell, MessageObject message) {
        if (cell == null || message == null || message.messageOwner == null || cell.getMessageObject() != message
                || cell.getScaleX() != 1f || cell.getScaleY() != 1f || cell.getTranslationX() != 0f
                || cell.getTransitionParams().animateChangeProgress != 1f || message.isSponsored()
                || message.getGroupIdForUse() != 0 || cell.getCurrentBackgroundDrawable(false) == null) return false;
        boolean spoiler=false;
        if (message.messageOwner.entities != null) for (TLRPC.MessageEntity entity : message.messageOwner.entities)
            if (entity instanceof TLRPC.TL_messageEntitySpoiler) { spoiler=true;break; }
        if (!BubbleTouchPolicy.mayConvertToSticker(true,
                cell.isAttachedToWindow() && cell.isShown() && cell.getAlpha()==1f,
                message.messageOwner.noforwards || !message.messageOwner.restriction_reason.isEmpty(),
                message.isEphemeral() || message.messageOwner.ttl!=0,spoiler,
                message.type==MessageObject.TYPE_TEXT && (message.messageOwner.media==null
                    || message.messageOwner.media instanceof TLRPC.TL_messageMediaEmpty),true)) return false;
        Rect visible = new Rect();
        Rect bounds = bounds(cell);
        if (!cell.getLocalVisibleRect(visible) || bounds.isEmpty() || !visible.contains(bounds)) return false;
        try { BubbleStickerSpec.dimensions(bounds.width(), bounds.height()); }
        catch (IllegalArgumentException unsupported) { return false; }
        return true;
    }
    private static Rect bounds(ChatMessageCell cell) {
        return new Rect(cell.getBackgroundDrawableLeft(), cell.getBackgroundDrawableTop()+cell.getPaddingTop(),
                cell.getBackgroundDrawableRight(), cell.getBackgroundDrawableBottom()+cell.getPaddingTop());
    }
    public NativeBubbleStickerPainter(ChatMessageCell cell, MessageObject message) {
        if (!eligible(cell, message)) throw new IllegalArgumentException("Native bubble not fully available");
        this.cell = cell; this.message = message; this.bounds = bounds(cell);
    }
    @Override public int width() { return bounds.width(); }
    @Override public int height() { return bounds.height(); }
    @Override public void drawOriginalBubble(Canvas canvas) {
        if (!eligible(cell, message) || !bounds.equals(bounds(cell))) throw new IllegalStateException("Rebound or moved bubble");
        int save = canvas.save();
        boolean wasExport=cell.drawForSignatureExport;
        cell.drawForSignatureExport=true;
        try {
            canvas.translate(-bounds.left, -bounds.top);
            canvas.clipRect(bounds);
            // Same native passes used by ChatActivity's selected-message scrim.
            // Gradient/wallpaper backgrounds deliberately skip the child's onDraw.
            if(cell.drawBackgroundInParent()) {
                int background=canvas.save();
                canvas.translate(0,cell.getPaddingTop());
                cell.drawBackgroundInternal(canvas,true);
                canvas.restoreToCount(background);
            }
            cell.draw(canvas);
            if(cell.hasOutboundsContent()) {
                int content=canvas.save();
                canvas.translate(0,cell.getPaddingTop());
                cell.drawOutboundsContent(canvas);
                canvas.restoreToCount(content);
            }
        } finally {
            cell.drawForSignatureExport=wasExport;
            canvas.restoreToCount(save);
        }
    }
}
