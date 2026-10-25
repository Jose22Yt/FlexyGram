package app.flexygram.header;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import org.telegram.ui.ActionBar.Theme;

/** Shared by the real header and synthetic settings preview. No blur, shaders or frame allocations. */
public final class HeaderSurface {
    private final RectF backSurface = new RectF();
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    public void draw(Canvas canvas, HeaderGeometry g, float density, Theme.ResourcesProvider provider) {
        int color = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
        fill.setColor((color & 0xffffff) | (Math.round(HeaderConfig.opacity() * 2.55f) << 24));
        stroke.setStyle(Paint.Style.STROKE); stroke.setStrokeWidth(Math.max(1, density * .65f));
        stroke.setColor((Theme.getColor(Theme.key_divider, provider) & 0xffffff) | 0x66000000);
        if (g.separateCount) {
            backSurface.set(g.back);
            if (org.telegram.messenger.LocaleController.isRTL) backSurface.left = backSurface.right - g.back.height();
            else backSurface.right = backSurface.left + g.back.height();
            piece(canvas, backSurface); piece(canvas, g.badge);
        } else piece(canvas, g.back);
        piece(canvas, g.title); piece(canvas, g.avatar);
    }
    private void piece(Canvas c, RectF r) { float radius = r.height() / 2; c.drawRoundRect(r, radius, radius, fill); c.drawRoundRect(r, radius, radius, stroke); }
}
