package app.flexygram.settings.signature;

import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.drawable.Drawable;
import org.telegram.ui.ActionBar.Theme;

/** Local presentation palette. Never mutates the user's theme or chat colours. */
public final class SettingsTheme implements Theme.ResourcesProvider {
    private final Theme.ResourcesProvider source;
    private SettingsTheme(Theme.ResourcesProvider source) { this.source = source; }
    public static Theme.ResourcesProvider wrap(Theme.ResourcesProvider source) {
        return source instanceof SettingsTheme ? source : new SettingsTheme(source);
    }
    public static java.util.ArrayList<org.telegram.ui.ActionBar.ThemeDescription> bind(
            org.telegram.ui.ActionBar.BaseFragment owner,
            org.telegram.ui.Components.RecyclerListView list,
            java.util.ArrayList<org.telegram.ui.ActionBar.ThemeDescription> descriptions) {
        org.telegram.ui.ActionBar.ThemeDescription.ThemeDescriptionDelegate update = () ->
                refresh(owner.getFragmentView(), owner.getActionBar(), list, owner.getResourceProvider());
        for (int key : new int[]{Theme.key_windowBackgroundGray, Theme.key_windowBackgroundWhite,
                Theme.key_windowBackgroundWhiteBlueHeader, Theme.key_windowBackgroundWhiteBlackText}) {
            descriptions.add(new org.telegram.ui.ActionBar.ThemeDescription(list, 0, null, null, null, update, key));
        }
        return descriptions;
    }
    public static void refresh(android.view.View page, org.telegram.ui.ActionBar.ActionBar bar,
                               org.telegram.ui.Components.RecyclerListView list, Theme.ResourcesProvider provider) {
        if (!(provider instanceof SettingsTheme)) return;
        int background = Theme.getColor(Theme.key_windowBackgroundGray, provider);
        if (page != null) page.setBackgroundColor(background);
        if (bar != null) {
            bar.setBackgroundColor(background);
            int text = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, provider);
            bar.setItemsColor(text, false);
            bar.setTitleColor(text);
        }
        if (list == null) return;
        int surface = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
        for (int i=0; i<list.getChildCount(); i++) {
            android.view.View child = list.getChildAt(i);
            if (child.getBackground() instanceof android.graphics.drawable.ColorDrawable
                    && !org.telegram.ui.Components.RecyclerListView.TAG_NOT_SECTION.equals(child.getTag())) {
                ((android.graphics.drawable.ColorDrawable)child.getBackground()).setColor(surface);
            }
        }
        list.invalidateViews();
    }
    private int original(int key) { return Theme.getColor(key, source); }
    @Override public int getColor(int key) {
        if (key == Theme.key_windowBackgroundGray || key == Theme.key_actionBarDefault) {
            return isDark() ? 0xff000000 : original(key);
        }
        if (key == Theme.key_windowBackgroundWhite) {
            return SettingsCardStyle.surface(original(key), original(Theme.key_windowBackgroundGray),
                    original(Theme.key_windowBackgroundWhiteBlueHeader), isDark());
        }
        return original(key);
    }
    @Override public boolean isDark() { return source == null ? Theme.isCurrentThemeDark() : source.isDark(); }
    @Override public int getCurrentColor(int key) { return getColor(key); }
    @Override public void setAnimatedColor(int key, int color) { if (source != null) source.setAnimatedColor(key, color); }
    @Override public Drawable getDrawable(String key) { return source == null ? null : source.getDrawable(key); }
    @Override public Paint getPaint(String key) { return source == null ? Theme.getThemePaint(key) : source.getPaint(key); }
    @Override public boolean hasGradientService() { return source != null && source.hasGradientService(); }
    @Override public void applyServiceShaderMatrix(int w,int h,float x,float y) {
        if(source == null) Theme.applyServiceShaderMatrix(w,h,x,y); else source.applyServiceShaderMatrix(w,h,x,y);
    }
    @Override public ColorFilter getAnimatedEmojiColorFilter() {
        return source == null ? Theme.chat_animatedEmojiTextColorFilter : source.getAnimatedEmojiColorFilter();
    }
}
