package app.exteraless.settings.utils;

import android.content.Context;

import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCell;

/** Settings-only navigation rows: 32dp native colour tiles, without changing touch targets. */
public class CompactSettingsTextCell extends TextCell {

    public CompactSettingsTextCell(Context context, Theme.ResourcesProvider resourcesProvider) {
        super(context, resourcesProvider);
    }

    @Override
    public void setTextAndIcon(CharSequence text, int icon, boolean divider) {
        super.setTextAndIcon(text, SettingsIcons.resolve(getContext(), icon), divider);
        styleIcon(icon);
    }

    @Override
    public void setTextAndValueAndIcon(CharSequence text, CharSequence value, boolean animated, int icon, boolean divider) {
        super.setTextAndValueAndIcon(text, value, animated, SettingsIcons.resolve(getContext(), icon), divider);
        styleIcon(icon);
    }

    @Override
    public void setTextAndSpoilersValueAndIcon(String text, CharSequence value, int icon, boolean divider) {
        super.setTextAndSpoilersValueAndIcon(text, value, SettingsIcons.resolve(getContext(), icon), divider);
        styleIcon(icon);
    }

    @Override
    public void setTextAndCheckAndIcon(CharSequence text, boolean checked, int icon, boolean divider) {
        super.setTextAndCheckAndIcon(text, checked, SettingsIcons.resolve(getContext(), icon), divider);
        styleIcon(icon);
    }

    @Override
    public void setColorfulIcon(int top, int bottom, int icon) {
        imageView.setImageDrawable(app.flexygram.settings.signature.SettingsCategoryIcon.create(getContext(),SettingsIcons.resolve(getContext(),icon),top,bottom));
        imageView.setBackground(null);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        // Binding and recycling reset TextCell's icon flags. Normalize after binding,
        // before its measurement, so large intrinsic drawables cannot enlarge the icon.
        setIsIcon(false);
        setImageLeft(20);
        setOffsetFromImage(64);
        imageView.setBackground(null);
        imageView.setPadding(0, 0, 0, 0);
        imageView.setTranslationX(0);
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
    }

    private void styleIcon(int resource){
        imageView.setImageDrawable(app.flexygram.settings.signature.SettingsCategoryIcon.create(getContext(),SettingsIcons.resolve(getContext(),resource)));
        imageView.setBackground(null);
    }
}
