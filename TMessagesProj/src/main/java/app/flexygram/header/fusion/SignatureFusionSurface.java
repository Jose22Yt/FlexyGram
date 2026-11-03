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
        if (!app.exteraless.appearance.FlexyGlassConfig.enabled()) {
            surfaceColor |= 0xFF000000;
            borderColor = 0;
        }
        float stroke = .7f * density;
        if (fill.getColor() != surfaceColor) fill.setColor(surfaceColor);
        if (border.getColor() != borderColor) border.setColor(borderColor);
        if (border.getStrokeWidth() != stroke) border.setStrokeWidth(stroke);
        if (separator.getColor() != separatorColor) separator.setColor(separatorColor);
        if (separator.getStrokeWidth() != stroke) separator.setStrokeWidth(stroke);
        drawPill(canvas,g.backVisual); if (g.separateUnread) drawPill(canvas,g.unread);
        drawCenterFill(canvas,g.center);
        drawActions(canvas,g);
        drawCenterBorder(canvas, g, borderColor, density);
        // The two separate native touch zones within one shared right mini-pill.
        if (g.callAvailable && !g.mattePortrait) {
            float x = g.actions.centerX();
            float cy = g.actionsVisual.centerY();
            float inset = 10f*density;
            canvas.drawLine(x,g.actionsVisual.top+inset,
                    x,g.actionsVisual.bottom-inset,separator);
        }
    }
    /** Same background, but no center stroke until the native portrait has been composited. */
    public void drawBackdrop(Canvas canvas, SignatureFusionGeometry.Layout g,
                     int surfaceColor, int borderColor, int separatorColor, float density) {
        if (!app.exteraless.appearance.FlexyGlassConfig.enabled()) {
            surfaceColor |= 0xFF000000;
            borderColor = 0;
        }
        float stroke = .7f * density;
        if (fill.getColor() != surfaceColor) fill.setColor(surfaceColor);
        if (border.getColor() != borderColor) border.setColor(borderColor);
        if (border.getStrokeWidth() != stroke) border.setStrokeWidth(stroke);
        if (separator.getColor() != separatorColor) separator.setColor(separatorColor);
        if (separator.getStrokeWidth() != stroke) separator.setStrokeWidth(stroke);
        drawPill(canvas,g.backVisual); if (g.separateUnread) drawPill(canvas,g.unread); drawCenterFill(canvas,g.center); drawActions(canvas,g);
        if(g.callAvailable && !g.mattePortrait){float x=g.actions.centerX();
            canvas.drawLine(x,g.actionsVisual.top+10f*density,x,g.actionsVisual.bottom-10f*density,separator);}
    }
    private void drawActions(Canvas canvas, SignatureFusionGeometry.Layout g) {
        if (g.mattePortrait) {
            if (g.callAvailable) drawPill(canvas,g.callVisual);
            drawPill(canvas,g.moreVisual);
        } else drawPill(canvas,g.actionsVisual);
    }
    private void drawCenterFill(Canvas canvas, SignatureFusionGeometry.Rect r) {
        work.set(r.left,r.top,r.right,r.bottom);canvas.drawRoundRect(work,r.height()*.5f,r.height()*.5f,fill);
    }
    public void drawCenterBorder(Canvas canvas, SignatureFusionGeometry.Layout g, int color, float density) {
        if (!app.exteraless.appearance.FlexyGlassConfig.enabled()) return;
        float stroke = .7f * density;
        if (border.getColor() != color) border.setColor(color);
        if (border.getStrokeWidth() != stroke) border.setStrokeWidth(stroke);
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
