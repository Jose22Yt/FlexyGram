package app.flexygram.bubbles;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import org.telegram.ui.ActionBar.Theme;

/** Native service-message material, sampled in the chat root's coordinate space.
 * Owns only a scratch paint: the theme retains ownership of its bitmap, shader and filters. */
public final class ServiceBubbleSurface {
    private final Paint scratch = new Paint(Paint.ANTI_ALIAS_FLAG);

    public boolean draw(Canvas canvas, Path shape, Theme.ResourcesProvider provider,
                        int width, int height, float x, float y, int alpha, boolean selected) {
        if (width <= 0 || height <= 0) return false;
        if (provider != null) provider.applyServiceShaderMatrix(width, height, x, y);
        else Theme.applyServiceShaderMatrix(width, height, x, y);
        return drawMapped(canvas, shape, provider, alpha, selected);
    }

    public static int textColor(Theme.ResourcesProvider provider) {
        return Theme.getThemePaint(Theme.key_paint_chatActionText, provider).getColor();
    }

    public boolean drawMapped(Canvas canvas, Path shape, Theme.ResourcesProvider provider, int alpha, boolean selected) {
        drawLayer(canvas, shape, Theme.getThemePaint(selected
                ? Theme.key_paint_chatActionBackgroundSelected : Theme.key_paint_chatActionBackground, provider), alpha);
        if (provider != null ? provider.hasGradientService() : Theme.hasGradientService()) {
            drawLayer(canvas, shape, Theme.getThemePaint(Theme.key_paint_chatActionBackgroundDarken, provider), alpha);
        }
        return true;
    }

    private void drawLayer(Canvas canvas, Path shape, Paint source, int alpha) {
        scratch.set(source);
        scratch.setAlpha(Math.round(source.getAlpha() * Math.max(0, Math.min(255, alpha)) / 255f));
        canvas.drawPath(shape, scratch);
    }
}
