package app.flexygram.effects;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import app.flexygram.bubbles.BubbleFusion;

/** The bubble contour/fusion bands applied to existing circles, pills and cards.
 * Geometry and hit targets remain native. No bitmap, shader, capture or animation is created here. */
public final class GlassContour {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final BubbleFusion fusion = new BubbleFusion();
    public GlassContour() {
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeCap(Paint.Cap.ROUND); paint.setStrokeJoin(Paint.Join.ROUND);
    }
    public void draw(Canvas canvas, Path path, Rect bounds, GlassSettings settings, float width,
                     int edgeColor, int fillColor, int alpha) {
        if (!settings.enabled || width <= 0 || settings.edge == 0 || alpha <= 0 || bounds.isEmpty()) return;
        // A wide border cannot consume more than one eighth of a compact control's diameter.
        float stroke = Math.min(width * 2, Math.min(bounds.width(), bounds.height()) * .25f);
        int edge = (edgeColor & 0xffffff) | (Math.round((edgeColor >>> 24) * alpha / 255f) << 24);
        paint.setStrokeWidth(stroke); paint.setColor(edge);
        canvas.save(); canvas.clipPath(path);
        if (settings.position == 1) canvas.clipRect(bounds.left, bounds.top, bounds.right, bounds.exactCenterY());
        else if (settings.position == 2) canvas.clipRect(bounds.left, bounds.exactCenterY(), bounds.right, bounds.bottom);
        else if (settings.position == 3) canvas.clipRect(bounds.left, bounds.top, bounds.exactCenterX(), bounds.bottom);
        else if (settings.position == 4) canvas.clipRect(bounds.exactCenterX(), bounds.top, bounds.right, bounds.bottom);
        if (settings.fusion == 2) {
            fusion.draw(canvas, path, paint, stroke, edge, fillColor, settings.fusionIntensity, settings.fusionAdapt);
        } else if (settings.fusion == 1 && settings.fusionIntensity > 0) {
            float strength = settings.fusionIntensity / 100f;
            int blended = settings.fusionAdapt ? BubbleFusion.mix(fillColor, edge, 55) : edge;
            paint.setStrokeWidth(stroke * 3); paint.setColor((blended & 0xffffff) | (Math.round((edge >>> 24) * .12f * strength) << 24));
            canvas.drawPath(path, paint);
            paint.setStrokeWidth(stroke * 2); paint.setColor((blended & 0xffffff) | (Math.round((edge >>> 24) * .26f * strength) << 24));
            canvas.drawPath(path, paint);
        }
        paint.setStrokeWidth(stroke); paint.setColor(edge); canvas.drawPath(path, paint);
        canvas.restore();
    }
}
