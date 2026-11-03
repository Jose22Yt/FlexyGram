package app.exteraless.settings.utils;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffColorFilter;

import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCell;

/** Settings-only navigation rows: 24dp outline icons, without changing touch targets. */
public class CompactSettingsTextCell extends TextCell {
    private final Theme.ResourcesProvider settingsResourcesProvider;
    private PorterDuffColorFilter iconFilter;
    private int iconColor;

    public CompactSettingsTextCell(Context context, Theme.ResourcesProvider resourcesProvider) {
        super(context, resourcesProvider);
        settingsResourcesProvider = resourcesProvider;
    }

    @Override
    public void setTextAndIcon(CharSequence text, int icon, boolean divider) {
        super.setTextAndIcon(text, SettingsIcons.resolve(getContext(), icon), divider);
    }

    @Override
    public void setTextAndValueAndIcon(CharSequence text, CharSequence value, boolean animated, int icon, boolean divider) {
        super.setTextAndValueAndIcon(text, value, animated, SettingsIcons.resolve(getContext(), icon), divider);
    }

    @Override
    public void setTextAndSpoilersValueAndIcon(String text, CharSequence value, int icon, boolean divider) {
        super.setTextAndSpoilersValueAndIcon(text, value, SettingsIcons.resolve(getContext(), icon), divider);
    }

    @Override
    public void setTextAndCheckAndIcon(CharSequence text, boolean checked, int icon, boolean divider) {
        super.setTextAndCheckAndIcon(text, checked, SettingsIcons.resolve(getContext(), icon), divider);
    }

    @Override
    public void setColorfulIcon(int top, int bottom, int icon) {
        // Navigation icons share one foreground; settings values/checks keep their colors.
        imageView.setImageResource(SettingsIcons.resolve(getContext(), icon));
        imageView.setBackground(null);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        // Binding and recycling reset TextCell's icon flags. Normalize after binding,
        // before its measurement, so large intrinsic drawables cannot enlarge the icon.
        setIsIcon(true);
        setImageLeft(20);
        setOffsetFromImage(60);
        imageView.setBackground(null);
        imageView.setPadding(0, 0, 0, 0);
        imageView.setTranslationX(0);
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
    }

    @Override
    protected void dispatchDraw(Canvas canvas) {
        // Read the active foreground at draw time: existing rows update on day/night
        // transitions without requiring their text or value to change.
        final int color = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, settingsResourcesProvider);
        if (iconFilter == null || iconColor != color) {
            iconColor = color;
            iconFilter = new PorterDuffColorFilter(color, PorterDuff.Mode.SRC_IN);
        }
        if (imageView.getColorFilter() != iconFilter) {
            imageView.setColorFilter(iconFilter);
        }
        super.dispatchDraw(canvas);
    }
}
