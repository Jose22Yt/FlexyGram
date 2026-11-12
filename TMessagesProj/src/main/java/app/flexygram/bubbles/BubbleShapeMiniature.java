/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.MessageDrawable;
import org.telegram.ui.ActionBar.Theme;

/** Tiny real bubble silhouettes; no wallpaper, observers, text layout or animation loop. */
public final class BubbleShapeMiniature extends View {
    private final MessageDrawable incoming = new MessageDrawable(MessageDrawable.TYPE_TEXT, false, false);
    private final MessageDrawable outgoing = new MessageDrawable(MessageDrawable.TYPE_TEXT, true, false);
    private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
    public BubbleShapeMiniature(Context context, int shape) {
        super(context); incoming.setFlexyBubbleShapePreview(shape); outgoing.setFlexyBubbleShapePreview(shape);
        line.setStrokeCap(Paint.Cap.ROUND);
    }
    private int dp(int value) { return AndroidUtilities.dp(value); }
    @Override protected void onMeasure(int widthSpec, int heightSpec) { setMeasuredDimension(MeasureSpec.getSize(widthSpec), dp(104)); }
    @Override protected void onSizeChanged(int w, int h, int ow, int oh) {
        incoming.setBounds(dp(8),dp(4),Math.max(dp(80),w-dp(100)),dp(50));
        outgoing.setBounds(dp(100),dp(54),Math.max(dp(180),w-dp(8)),dp(100));
        incoming.setTop(0,w,h,false,false);outgoing.setTop(0,w,h,false,false);
    }
    @Override protected void onDraw(Canvas canvas) {
        incoming.draw(canvas);outgoing.draw(canvas);
        line.setStrokeWidth(dp(4));line.setColor(Theme.getColor(Theme.key_chat_messageTextIn));
        canvas.drawLine(dp(28),dp(27),Math.max(dp(44),getWidth()-dp(140)),dp(27),line);
        line.setColor(Theme.getColor(Theme.key_chat_messageTextOut));
        canvas.drawLine(dp(126),dp(77),Math.max(dp(142),getWidth()-dp(40)),dp(77),line);
    }
}
