/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;

/** Reused canvas primitives; no blur, render layers or frame-driven animators. */
public final class SignatureHomePainter {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF bounds = new RectF();

    public void control(Canvas canvas, float cx, float cy, float diameter, float density,
                        boolean dark, boolean glass, float alpha) {
        if (diameter <= 0 || alpha <= 0) return;
        float r = diameter / 2;
        bounds.set(cx - r, cy - r, cx + r, cy + r);
        surface(canvas, r, density, dark, SignatureHomeStyle.surface(dark, glass), alpha, app.exteraless.appearance.UniversalGlass.SEARCH);
    }

    public void category(Canvas canvas, float width, float height, float density,
                         boolean dark, boolean glass, float selection) {
        category(canvas,width,height,density,dark,glass,selection,SignatureHomeStyle.selectedSurface(dark,glass));
    }

    public void category(Canvas canvas,float width,float height,float density,boolean dark,boolean glass,
                         float selection,int selectedColor) {
        float h = SignatureHomeStyle.categoryHeight(height, density);
        // Inset each native cell, including RTL and reordered/animated cells.
        // No item decoration changes positions or filter hit testing.
        bounds.set(3 * density, (height - h) / 2, width - 3 * density, (height + h) / 2);
        if (bounds.width() <= 0 || h <= 0) return;
        int color = blend(SignatureHomeStyle.surface(dark, glass),
                selectedColor, selection);
        surface(canvas, h / 2, density, dark, color, 1, app.exteraless.appearance.UniversalGlass.FOLDERS);
    }

    private void surface(Canvas canvas, float radius, float density, boolean dark, int color, float alpha, int scope) {
        boolean effects = app.exteraless.appearance.FlexyGlassConfig.enabled();
        boolean custom = app.exteraless.appearance.UniversalGlass.enabled(scope);
        if (custom) {
            int a = Math.round(app.exteraless.appearance.UniversalGlassConfig.opacity() * 2.55f);
            color = dark ? (color & 0xffffff) | (Math.round(a * .85f) << 24)
                    : app.exteraless.appearance.GlassContrastPolicy.lightSurface(color, a);
        }
        if (!effects) color |= 0xFF000000;
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(color);
        paint.setAlpha(Math.round((color >>> 24) * Math.max(0, Math.min(1, alpha))));
        canvas.drawRoundRect(bounds, radius, radius, paint);
        if (!effects) return;
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(custom ? density * app.exteraless.appearance.UniversalGlassConfig.snapshot().width / 10f : Math.max(1, density * .5f));
        if (paint.getStrokeWidth() <= 0) return;
        color = custom ? app.exteraless.appearance.UniversalGlass.edgeColor(true, dark) : SignatureHomeStyle.edge(dark);
        paint.setColor(color);
        paint.setAlpha(Math.round((color >>> 24) * Math.max(0, Math.min(1, alpha))));
        // Keep the stroke inside the allocated surface.
        float inset = paint.getStrokeWidth() / 2;
        bounds.inset(inset, inset);
        float innerRadius = Math.max(0, radius - inset);
        canvas.drawRoundRect(bounds, innerRadius, innerRadius, paint);
    }

    public static int blend(int from, int to, float progress) {
        float p = Math.max(0, Math.min(1, progress));
        int color = 0;
        for (int shift = 0; shift <= 24; shift += 8) {
            int a = (from >>> shift) & 255, b = (to >>> shift) & 255;
            color |= Math.round(a + (b - a) * p) << shift;
        }
        return color;
    }
}
