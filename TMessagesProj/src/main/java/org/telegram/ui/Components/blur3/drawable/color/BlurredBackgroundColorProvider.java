package org.telegram.ui.Components.blur3.drawable.color;

import androidx.annotation.ColorInt;

import org.telegram.ui.ActionBar.Theme;

public interface BlurredBackgroundColorProvider {
    default boolean isDarkAppearance() { return Theme.isCurrentThemeDark(); }
    @ColorInt int getShadowColor();
    @ColorInt int getBackgroundColor();
    @ColorInt int getStrokeColorTop();
    @ColorInt int getStrokeColorBottom();

    /**
     * Цвет сплошного контура (режим {@code GlassOutlineStyle.SOLID}).
     * По умолчанию цвет разделителя.
     */
    @ColorInt default int getStrokeColorFull() {
        return Theme.getDividerColor(null);
    }
}
