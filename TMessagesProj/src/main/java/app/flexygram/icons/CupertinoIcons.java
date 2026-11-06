package app.flexygram.icons;

import android.content.res.Resources;
import android.graphics.drawable.Drawable;
import app.exteraless.icons.BaseIconPacks;

/** Cupertino is the built-in default. Explicit Solar/Remix/user packs keep their precedence. */
public final class CupertinoIcons {
    private CupertinoIcons() {}
    public static Drawable create(Resources resources, int id) {
        int spec = CupertinoIconMap.spec(id);
        if (spec == 0 || BaseIconPacks.getSelected() != BaseIconPacks.BASE_DEFAULT) return null;
        return spec == 0 ? null : new CupertinoGlyphDrawable(resources, spec,CupertinoIconMap.color(id));
    }
}
