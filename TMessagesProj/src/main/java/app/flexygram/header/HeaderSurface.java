package app.flexygram.header;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import org.telegram.ui.ActionBar.Theme;

/** Shared by the real header and synthetic settings preview. No blur, shaders or frame allocations. */
public final class HeaderSurface {
    private final RectF backSurface = new RectF();
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private int lastBaseColor, lastDividerColor, lastOpacity = -1;
    private boolean lastEffects, hasCachedState;
    private float lastDensity = -1f;

    public HeaderSurface() {
        stroke.setStyle(Paint.Style.STROKE);
    }

    public void draw(Canvas canvas, HeaderGeometry g, float density, Theme.ResourcesProvider provider) {
        int color = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
        boolean effects = org.telegram.messenger.SharedConfig.chatBlurEnabled();
        int opacity = HeaderConfig.opacity();
        int dividerColor = effects ? Theme.getColor(Theme.key_divider, provider) : 0;

        if (!hasCachedState || color != lastBaseColor || effects != lastEffects || opacity != lastOpacity || dividerColor != lastDividerColor) {
            fill.setColor(effects ? (color & 0xffffff) | (Math.round(opacity * 2.55f) << 24) : color | 0xff000000);
            stroke.setColor(effects ? (dividerColor & 0xffffff) | 0x66000000 : 0);
            lastBaseColor = color;
            lastEffects = effects;
            lastOpacity = opacity;
            lastDividerColor = dividerColor;
            hasCachedState = true;
        }

        if (density != lastDensity) {
            stroke.setStrokeWidth(Math.max(1, density * .65f));
            lastDensity = density;
        }

        if (g.separateCount) {
            backSurface.set(g.back);
            if (org.telegram.messenger.LocaleController.isRTL) backSurface.left = backSurface.right - g.back.height();
            else backSurface.right = backSurface.left + g.back.height();
            piece(canvas, backSurface); piece(canvas, g.badge);
        } else piece(canvas, g.back);
        piece(canvas, g.title); piece(canvas, g.avatar);
    }

    private void piece(Canvas c, RectF r) {
        if (r.width() <= 0 || r.height() <= 0) return;
        float radius = r.height() / 2;
        c.drawRoundRect(r, radius, radius, fill);
        if (lastEffects) c.drawRoundRect(r, radius, radius, stroke);
    }
}
