package app.flexygram.header;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import org.telegram.ui.ActionBar.Theme;

/** Shared by the real header and synthetic settings preview. No blur, shaders or frame allocations. */
public final class HeaderSurface {
    private final RectF backSurface = new RectF();
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), stroke = new Paint(Paint.ANTI_ALIAS_FLAG);

    public HeaderSurface() {
        stroke.setStyle(Paint.Style.STROKE);
    }

    public void draw(Canvas canvas, HeaderGeometry g, float density, Theme.ResourcesProvider provider) {
        int color = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
        boolean effects = app.exteraless.appearance.FlexyGlassConfig.enabled();
        fill.setColor(effects ? (color & 0xffffff) | (Math.round(HeaderConfig.opacity() * 2.55f) << 24) : color | 0xFF000000);
        boolean custom = app.exteraless.appearance.UniversalGlass.enabled(app.exteraless.appearance.UniversalGlass.HEADER);
        if (custom) fill.setColor(app.exteraless.appearance.UniversalGlass.backgroundColor(provider, Theme.key_windowBackgroundWhite));
        float strokeWidth = custom ? density * app.exteraless.appearance.UniversalGlassConfig.snapshot().width / 10f : Math.max(1, density * .65f);
        if (stroke.getStrokeWidth() != strokeWidth) stroke.setStrokeWidth(strokeWidth);
        stroke.setColor(effects ? (Theme.getColor(Theme.key_divider, provider) & 0xffffff) | 0x66000000 : 0);
        if (custom) stroke.setColor(strokeWidth > 0 ? app.exteraless.appearance.UniversalGlass.edgeColor(true) : 0);
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
