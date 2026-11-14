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
        Drawable exact = ExactIcons.create(this, id, density, theme);
        if (exact != null) return exact;
        // ExactIcons already covers both Default and Cupertino. A second lookup
        // only repeats map/config work for resources which have no replacement.
        return super.getDrawableForDensity(id, density, theme);
    }
}
