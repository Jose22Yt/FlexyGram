package app.flexygram.header.fusion;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;

/**
 * Stateless surfaces with reused Paint and RectF. No embedded click handling,
 * no polling and no bitmap/shader allocations in draw(). All native buttons,
 * avatar resources and title/subtitle remain owned by Telegram's host views.
 */
public final class SignatureFusionSurface {
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint border = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint separator = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF work = new RectF();

    public SignatureFusionSurface() {
        border.setStyle(Paint.Style.STROKE);
        separator.setStyle(Paint.Style.STROKE);
    }

    public void draw(Canvas canvas, SignatureFusionGeometry.Layout g,
                     int surfaceColor, int borderColor, int separatorColor, float density) {
        fill.setColor(surfaceColor);
        border.setColor(borderColor);
        border.setStrokeWidth(.7f * density);
        separator.setColor(separatorColor);
        separator.setStrokeWidth(.7f * density);
        drawPill(canvas,g.back);
        drawCenterFill(canvas,g.center);
        drawPill(canvas,g.actions);
        drawCenterBorder(canvas, g, borderColor, density);
        // The two separate native touch zones within one shared right mini-pill.
        if (g.callAvailable) {
            float x = g.more.left == g.actions.left ? g.more.right : g.call.right;
            float cy = g.actions.centerY();
            float inset = 10f*density;
            canvas.drawLine(x,cy-g.actions.height()*.5f+inset,
                    x,cy+g.actions.height()*.5f-inset,separator);
        }
    }
    /** Same background, but no center stroke until the native portrait has been composited. */
    public void drawBackdrop(Canvas canvas, SignatureFusionGeometry.Layout g,
                     int surfaceColor, int borderColor, int separatorColor, float density) {
        fill.setColor(surfaceColor); border.setColor(borderColor); border.setStrokeWidth(.7f * density);
        separator.setColor(separatorColor); separator.setStrokeWidth(.7f * density);
        drawPill(canvas,g.back); drawCenterFill(canvas,g.center); drawPill(canvas,g.actions);
        if(g.callAvailable){float x=g.more.left==g.actions.left?g.more.right:g.call.right;float cy=g.actions.centerY();
            canvas.drawLine(x,cy-g.actions.height()*.5f+10f*density,x,cy+g.actions.height()*.5f-10f*density,separator);}
    }
    private void drawCenterFill(Canvas canvas, SignatureFusionGeometry.Rect r) {
        work.set(r.left,r.top,r.right,r.bottom);canvas.drawRoundRect(work,r.height()*.5f,r.height()*.5f,fill);
    }
    public void drawCenterBorder(Canvas canvas, SignatureFusionGeometry.Layout g, int color, float density) {
        border.setColor(color);border.setStrokeWidth(.7f*density);
        var r=g.center;work.set(r.left,r.top,r.right,r.bottom);work.inset(border.getStrokeWidth()*.5f,border.getStrokeWidth()*.5f);
        canvas.drawRoundRect(work,r.height()*.5f,r.height()*.5f,border);
    }
    private void drawPill(Canvas canvas, SignatureFusionGeometry.Rect r) {
        work.set(r.left,r.top,r.right,r.bottom);
        float radius = Math.max(0f,r.height()*.5f);
        canvas.drawRoundRect(work,radius,radius,fill);
        canvas.drawRoundRect(work,radius,radius,border);
    }
}
