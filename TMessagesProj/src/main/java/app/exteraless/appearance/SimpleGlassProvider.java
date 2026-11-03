package app.exteraless.appearance;

import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProvider;

/** Marks the original material's customizable thickness; keeps its colors, shadows and native outline style. */
public final class SimpleGlassProvider implements BlurredBackgroundProvider {
    private final BlurredBackgroundProvider delegate;
    public SimpleGlassProvider(BlurredBackgroundProvider delegate) { this.delegate = delegate; }
    public int getShadowColor() { return delegate.getShadowColor(); }
    public int getBackgroundColor() { return delegate.getBackgroundColor(); }
    public int getStrokeColorTop() { return delegate.getStrokeColorTop(); }
    public int getStrokeColorBottom() { return delegate.getStrokeColorBottom(); }
    public int getStrokeColorFull() { return delegate.getStrokeColorFull(); }
    public float getStrokeWidthTop() { return delegate.getStrokeWidthTop(); }
    public float getStrokeWidthBottom() { return delegate.getStrokeWidthBottom(); }
    public float getShadowRadius() { return delegate.getShadowRadius(); }
    public float getShadowDx() { return delegate.getShadowDx(); }
    public float getShadowDy() { return delegate.getShadowDy(); }
}
