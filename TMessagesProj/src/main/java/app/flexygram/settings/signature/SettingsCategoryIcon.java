package app.flexygram.settings.signature;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import org.telegram.messenger.AndroidUtilities;

/** Theme-tinted settings glyph: no colour tile, layers, animation or per-frame allocation. */
public final class SettingsCategoryIcon extends Drawable implements Drawable.Callback, app.flexygram.icons.IconPressFeedback.Target {
    private final Drawable glyph;
    public boolean isStandalone() { return true; }
    @Override public void setIconPressScale(float scale) {}
    public static Drawable create(Context context, int resource) {
        return resource <= 0 ? null : new SettingsCategoryIcon(context, resource);
    }
    public static Drawable create(Context context, int resource, int top, int bottom) {
        return create(context, resource);
    }
    private SettingsCategoryIcon(Context context, int resource) {
        Drawable source = context.getDrawable(resource);
        glyph = source == null ? null : source.mutate();
        if (glyph != null) glyph.setCallback(this);
    }
    @Override protected void onBoundsChange(Rect bounds) { if (glyph != null) glyph.setBounds(bounds); }
    @Override public void draw(Canvas canvas) { if (glyph != null) glyph.draw(canvas); }
    @Override public void setAlpha(int alpha) { if (glyph != null) glyph.setAlpha(alpha); invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter filter) { if (glyph != null) glyph.setColorFilter(filter); invalidateSelf(); }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    @Override public int getIntrinsicWidth() { return AndroidUtilities.dp(SettingsCardStyle.ICON); }
    @Override public int getIntrinsicHeight() { return AndroidUtilities.dp(SettingsCardStyle.ICON); }
    @Override public void invalidateDrawable(Drawable who) { invalidateSelf(); }
    @Override public void scheduleDrawable(Drawable who, Runnable what, long when) { scheduleSelf(what, when); }
    @Override public void unscheduleDrawable(Drawable who, Runnable what) { unscheduleSelf(what); }
}
