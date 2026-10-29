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
    private boolean reduceOptics;
    private boolean geometryReady;
    private float lastX, lastY, lastWidth, lastHeight, lastStretch, lastDirection;
    public Path shape() { return shape; }
    public Drawable backdrop() { return backdrop; }
    public void backdrop(Drawable value) { backdrop = value; }
    public void prepare(float x, float y, float width, float height, float stretch, float direction) {
        reduceOptics=LiquidNavigationConfig.adaptiveQuality()&&stretch>.12f;
        if (geometryReady && x == lastX && y == lastY && width == lastWidth && height == lastHeight
                && stretch == lastStretch && direction == lastDirection) return;
        geometryReady = true;
        lastX=x; lastY=y; lastWidth=width; lastHeight=height; lastStretch=stretch; lastDirection=direction;
        float halfH=Math.max(0,height*.5f), halfW=Math.max(height*1.55f,width)*.5f;
        bounds.set(x - halfW, y - halfH, x + halfW, y + halfH);
        // Signed head/tail curvature changes immediately on reversal; outer capsule stays fixed.
        float skew = Math.max(-1f, Math.min(1f, direction)) * Math.min(.19f, stretch);
        float leftH = halfH * (1f - skew * .8f);
        float rightH = halfH * (1f + skew * .8f);
        // A horizontal capsule, including during press and drag. Never an ellipse/circle.
        float radius=Math.min(halfH,halfW/1.55f), k=.5522848f;
        float left=bounds.left,right=bounds.right,top=bounds.top,bottom=bounds.bottom;
        float l=left+radius,r=right-radius;
        float leftRadius=radius*(1-skew*.3f),rightRadius=radius*(1+skew*.3f);
        shape.rewind();shape.moveTo(l,top);shape.lineTo(r,top);
        shape.cubicTo(r+rightRadius*k,top,right,y-rightH*k,right,y);
        shape.cubicTo(right,y+rightH*k,r+rightRadius*k,bottom,r,bottom);
        shape.lineTo(l,bottom);
        shape.cubicTo(l-leftRadius*k,bottom,left,y+leftH*k,left,y);
        shape.cubicTo(left,y-leftH*k,l-leftRadius*k,top,l,top);
        shape.close();
    }
    public void surface(Canvas canvas) {
        int save = canvas.save();
        canvas.clipPath(shape);
        if (backdrop != null && !reduceOptics) {
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
        return 1f + (reduceOptics?.12f:.42f) * LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.REFRACTION) / 100f;
    }
}
