package app.exteraless.appearance;

import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProvider;

/** Marks the original material's customizable thickness; keeps its colors, shadows and native outline style. */
public final class SimpleGlassProvider implements BlurredBackgroundProvider {
    private final BlurredBackgroundProvider delegate;
    private final org.telegram.ui.ActionBar.Theme.ResourcesProvider provider;
    private final int colorKey;
    public SimpleGlassProvider(BlurredBackgroundProvider delegate, org.telegram.ui.ActionBar.Theme.ResourcesProvider provider, int colorKey) {
        this.delegate = delegate; this.provider = provider; this.colorKey = colorKey;
    }
    private int styledEdge(int fallback, boolean top) {
        var settings = UniversalGlassConfig.snapshot();
        if (settings.look == 0) return fallback;
        boolean dark = provider != null ? provider.isDark() : org.telegram.ui.ActionBar.Theme.isCurrentThemeDark();
        int base = app.flexygram.bubbles.BubbleOutline.palette(org.telegram.ui.ActionBar.Theme.getColor(colorKey, provider),
                org.telegram.ui.ActionBar.Theme.getColor(org.telegram.ui.ActionBar.Theme.key_telegram_color, provider), 0, 0);
        int color = app.flexygram.bubbles.BubbleOutline.color(base, dark, settings.bubbleStyle(), settings.materialIntensity);
        int alpha = Math.min(255, Math.round((color >>> 24) * settings.edge / 100f * (top ? 1f : .72f)));
        return (color & 0xffffff) | (alpha << 24);
    }
    public int getShadowColor() { return delegate.getShadowColor(); }
    public int getBackgroundColor() { return delegate.getBackgroundColor(); }
    public int getStrokeColorTop() { return styledEdge(delegate.getStrokeColorTop(), true); }
    public int getStrokeColorBottom() { return styledEdge(delegate.getStrokeColorBottom(), false); }
    public int getStrokeColorFull() { return styledEdge(delegate.getStrokeColorFull(), true); }
    public float getStrokeWidthTop() { return delegate.getStrokeWidthTop(); }
    public float getStrokeWidthBottom() { return delegate.getStrokeWidthBottom(); }
    public float getShadowRadius() { return delegate.getShadowRadius(); }
    public float getShadowDx() { return delegate.getShadowDx(); }
    public float getShadowDy() { return delegate.getShadowDy(); }
}
