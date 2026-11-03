package app.exteraless.appearance;

import app.flexygram.effects.GlassSettings;
import org.telegram.ui.Components.blur3.GlassOutlineStyle;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProvider;

/** Material identity permits custom borders without changing legacy/third-party providers. */
public final class CustomGlassProvider implements BlurredBackgroundProvider {
    private final BlurredBackgroundProvider colors;
    public final GlassSettings settings;
    public CustomGlassProvider(BlurredBackgroundProvider colors, GlassSettings settings) {
        this.colors = colors;
        this.settings = settings;
    }
    public GlassOutlineStyle outline() {
        if (!FlexyGlassConfig.enabled() || settings.width == 0 || settings.edge == 0) return GlassOutlineStyle.HIDDEN;
        return settings.style == 0 ? GlassOutlineStyle.SOLID : GlassOutlineStyle.GLARE;
    }
    public int getBackgroundColor() { return colors.getBackgroundColor(); }
    public int getShadowColor() { return 0; }
    public int getStrokeColorTop() { return colors.getStrokeColorTop(); }
    public int getStrokeColorBottom() { return colors.getStrokeColorBottom(); }
    public int getStrokeColorFull() { return colors.getStrokeColorFull(); }
    public float getStrokeWidthTop() { return colors.getStrokeWidthTop(); }
    public float getStrokeWidthBottom() { return colors.getStrokeWidthBottom(); }
    public float getShadowRadius() { return 0; }
    public float getShadowDx() { return 0; }
    public float getShadowDy() { return 0; }
}
