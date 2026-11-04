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
    public void setResourcesProvider(Theme.ResourcesProvider provider) { this.provider=provider; }
    public void draw(Canvas canvas, RectF rect, float topRadius, float bottomRadius, float alpha) {
        int color=SettingsCardStyle.surface(Theme.getColor(Theme.key_windowBackgroundWhite,provider),
                Theme.getColor(Theme.key_windowBackgroundGray,provider));
        paint.setColor(Theme.multAlpha(color,alpha));
        if(topRadius==bottomRadius)canvas.drawRoundRect(rect,topRadius,topRadius,paint);
        else {
            path.rewind();
            radii[0]=radii[1]=radii[2]=radii[3]=topRadius;
            radii[4]=radii[5]=radii[6]=radii[7]=bottomRadius;
            path.addRoundRect(rect,radii,Path.Direction.CW);canvas.drawPath(path,paint);
        }
    }
}
