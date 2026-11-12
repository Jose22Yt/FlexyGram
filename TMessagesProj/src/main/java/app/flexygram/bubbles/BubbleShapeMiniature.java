/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.MessageDrawable;
import org.telegram.ui.ActionBar.Theme;

/** One real bubble per option; the full conversation preview owns the two-message example. */
public final class BubbleShapeMiniature extends View {
    private final MessageDrawable outgoing = new MessageDrawable(MessageDrawable.TYPE_TEXT, true, false);
    private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
    public BubbleShapeMiniature(Context context, int shape) {
        super(context); outgoing.setFlexyBubbleShapePreview(shape);
        line.setStrokeCap(Paint.Cap.ROUND);
    }
    private int dp(int value) { return AndroidUtilities.dp(value); }
    @Override protected void onMeasure(int widthSpec, int heightSpec) { setMeasuredDimension(MeasureSpec.getSize(widthSpec), dp(72)); }
    @Override protected void onSizeChanged(int w, int h, int ow, int oh) {
        outgoing.setBounds(dp(48),dp(8),Math.max(dp(96),w-dp(48)),dp(64));
        outgoing.setTop(0,w,h,false,false);
    }
    @Override protected void onDraw(Canvas canvas) {
        outgoing.draw(canvas);line.setStrokeWidth(dp(4));
        line.setColor(Theme.getColor(Theme.key_chat_messageTextOut));
        canvas.drawLine(dp(76),dp(36),Math.max(dp(92),getWidth()-dp(84)),dp(36),line);
    }
}
