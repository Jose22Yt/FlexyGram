package app.flexygram.settings.signature;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import org.telegram.ui.ActionBar.Theme;

/** Retained flat section painter; no blur, shadow, bitmap or allocation inside draw. */
public final class SettingsCardBackground {
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path=new Path();
    private final float[] radii=new float[8];
    private Theme.ResourcesProvider provider;
    private app.flexygram.effects.ChatEdgeReflection colorOsEdge;
    public void setResourcesProvider(Theme.ResourcesProvider provider) { this.provider=provider; }
    public void draw(Canvas canvas, RectF rect, float topRadius, float bottomRadius, float alpha) {
        final boolean dark = provider == null ? Theme.isCurrentThemeDark() : provider.isDark();
        int color=SettingsCardStyle.surface(Theme.getColor(Theme.key_windowBackgroundWhite,provider),
                Theme.getColor(Theme.key_windowBackgroundGray,provider),
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueHeader,provider),
                dark);
        paint.setColor(Theme.multAlpha(color,alpha));
        if(topRadius==bottomRadius)canvas.drawRoundRect(rect,topRadius,topRadius,paint);
        else {
            path.rewind();
            radii[0]=radii[1]=radii[2]=radii[3]=topRadius;
            radii[4]=radii[5]=radii[6]=radii[7]=bottomRadius;
            path.addRoundRect(rect,radii,Path.Direction.CW);canvas.drawPath(path,paint);
        }
        if (app.flexygram.effects.ChatEdgeStyle.isColorOsGlass()) {
            colorOsEdge = app.flexygram.effects.ChatEdgeStyle.updateReflection(colorOsEdge);
            final int edgeAlpha = Math.max(0, Math.min(255, Math.round(255f * alpha)));
            if (topRadius == bottomRadius) {
                colorOsEdge.draw(canvas, rect, topRadius, dark, edgeAlpha);
            } else {
                colorOsEdge.drawClipped(canvas, rect.left, rect.top, rect.right, rect.bottom, path, dark, edgeAlpha);
            }
        }
    }
}
