/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;

/** Independent neutral lens. Reuses the native GPU backdrop when available; never captures bitmaps. */
public final class LiquidLensRenderer {
    private final Path shape = new Path();
    private final RectF bounds = new RectF();
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private Drawable backdrop;
    public Path shape() { return shape; }
    public Drawable backdrop() { return backdrop; }
    public void backdrop(Drawable value) { backdrop = value; }
    public void prepare(float x, float y, float width, float height, float stretch, float direction) {
        float halfW = Math.max(0, width * .5f), halfH = Math.max(0, height * .5f);
        bounds.set(x - halfW, y - halfH, x + halfW, y + halfH);
        // Signed head/tail curvature changes immediately on reversal; outer capsule stays fixed.
        float skew = Math.max(-1f, Math.min(1f, direction)) * Math.min(.19f, stretch);
        float leftH = halfH * (1f - skew * .8f);
        float rightH = halfH * (1f + skew * .8f);
        float k = .58f;
        shape.rewind();
        shape.moveTo(x, y - halfH);
        shape.cubicTo(x + halfW*k, y-halfH, bounds.right, y-rightH*k, bounds.right, y);
        shape.cubicTo(bounds.right, y+rightH*k, x+halfW*k, y+halfH, x, y+halfH);
        shape.cubicTo(x-halfW*k, y+halfH, bounds.left, y+leftH*k, bounds.left, y);
        shape.cubicTo(bounds.left, y-leftH*k, x-halfW*k, y-halfH, x, y-halfH);
        shape.close();
    }
    public void surface(Canvas canvas) {
        int save = canvas.save();
        canvas.clipPath(shape);
        if (backdrop != null) {
            backdrop.setBounds((int)bounds.left, (int)bounds.top,
                    (int)Math.ceil(bounds.right), (int)Math.ceil(bounds.bottom));
            backdrop.draw(canvas);
        }
        // Fallback is a clear neutral lens, independent of the theme accent color.
        int tint = Math.round((100 - LiquidNavigationConfig.opacity()) * .30f
                * LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.INTENSITY) / 100f);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor((tint << 24) | 0x00ffffff);
        canvas.drawPath(shape, paint);
        canvas.restoreToCount(save);
    }
    public void rim(Canvas canvas, float density) {
        float strength = LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.INTENSITY) / 100f;
        int outline = Math.round(100 * strength
                * LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.OUTLINE) / 100f);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(Math.max(1f, density * .7f));
        paint.setColor((outline << 24) | 0x00ffffff);
        canvas.drawPath(shape, paint);
        int save = canvas.save();
        canvas.clipRect(bounds.left, bounds.top, bounds.right, bounds.top + bounds.height() * .38f);
        int reflection = Math.round(175 * strength
                * LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.REFLECTION) / 100f);
        paint.setColor((reflection << 24) | 0x00ffffff);
        paint.setStrokeWidth(Math.max(1f, density));
        canvas.drawPath(shape, paint);
        canvas.restoreToCount(save);
        paint.setStyle(Paint.Style.FILL);
    }
    public float magnification() {
        return 1f + .42f * LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.INTENSITY) / 100f;
    }
}
