package app.flexygram.header;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import app.flexygram.effects.ChatChromePalette;
import app.flexygram.effects.ChatEdgeReflection;
import org.telegram.ui.ActionBar.Theme;

/** Shared outline and fill geometry for the chat header and settings preview. */
public final class HeaderSurface {
    private final RectF backSurface = new RectF();
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean lastDark, hasCachedState;
    private float lastDensity = -1f;

    public HeaderSurface() {
        stroke.setStyle(Paint.Style.STROKE);
    }

    public void draw(Canvas canvas, HeaderGeometry g, float density, Theme.ResourcesProvider provider) {
        draw(canvas, g, density, provider, null);
    }

    public void draw(Canvas canvas, HeaderGeometry g, float density, Theme.ResourcesProvider provider,
            ChatEdgeReflection reflection) {
        final boolean dark = provider != null ? provider.isDark() : Theme.isCurrentThemeDark();
        if (!hasCachedState || dark != lastDark) {
            fill.setColor(ChatChromePalette.surface(dark));
            stroke.setColor(ChatChromePalette.outline(dark));
            lastDark = dark;
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
            piece(canvas, backSurface, reflection); piece(canvas, g.badge, reflection);
        } else piece(canvas, g.back, reflection);
        piece(canvas, g.title, reflection); piece(canvas, g.avatar, reflection);
    }

    private void piece(Canvas c, RectF r, ChatEdgeReflection reflection) {
        if (r.width() <= 0 || r.height() <= 0) return;
        float radius = r.height() / 2;
        c.drawRoundRect(r, radius, radius, fill);
        if (reflection == null) c.drawRoundRect(r, radius, radius, stroke);
        else reflection.draw(c, r, radius, lastDark, 255);
    }
}
