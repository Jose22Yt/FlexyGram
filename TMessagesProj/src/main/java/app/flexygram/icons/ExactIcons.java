package app.flexygram.icons;

import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import app.exteraless.icons.BaseIconPacks;

/** Default artwork from the user's archive. Resources owns decoding and bitmap reuse. */
public final class ExactIcons {
    private ExactIcons() {}

    public static Drawable create(Resources resources, int id, int density, Resources.Theme theme) {
        ExactIconMap.Entry entry = ExactIconMap.get(id);
        if (entry == null || BaseIconPacks.getSelected() != BaseIconPacks.BASE_DEFAULT) return null;
        // Asset IDs are deliberately outside the alias map: this lookup cannot recurse.
        // Android's density/configuration-aware resource cache shares the decoded pixels.
        Drawable source = resources.getDrawableForDensity(entry.asset, density, theme);
        if (!(source instanceof BitmapDrawable)) return null;
        return new Icon(resources, ((BitmapDrawable) source).getBitmap(), entry,
                density == 0 ? resources.getDisplayMetrics().densityDpi : density);
    }

    /** Independent tint/bounds per view, shared immutable pixels and original UI dimensions. */
    private static final class Icon extends BitmapDrawable {
        private final int width, height;
        Icon(Resources resources, Bitmap bitmap, ExactIconMap.Entry entry, int density) {
            super(resources, bitmap);
            width = Math.round(entry.width * density / 160f);
            height = Math.round(entry.height * density / 160f);
            setFilterBitmap(true);
            setTint(entry.color);
            setAutoMirrored(entry.mirrored);
        }
        @Override public int getIntrinsicWidth() { return width; }
        @Override public int getIntrinsicHeight() { return height; }
    }
}
