package app.flexygram.icons;

import android.content.res.Resources;
import android.graphics.drawable.Drawable;

/** Application/theme loaders also see the default icons, including non-Activity contexts. */
public final class CupertinoResources extends Resources {
    public CupertinoResources(Resources original) {
        super(original.getAssets(), original.getDisplayMetrics(), original.getConfiguration());
    }
    @Override public Drawable getDrawable(int id) { return getDrawableForDensity(id, 0, null); }
    @Override public Drawable getDrawable(int id, Theme theme) { return getDrawableForDensity(id, 0, theme); }
    @Override public Drawable getDrawableForDensity(int id, int density) { return getDrawableForDensity(id, density, null); }
    @Override public Drawable getDrawableForDensity(int id, int density, Theme theme) {
        Drawable icon = CupertinoIcons.create(this, id);
        return icon != null ? icon : super.getDrawableForDensity(id, density, theme);
    }
}
