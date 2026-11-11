/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.icons;

import android.content.Context;
import android.content.res.Resources;
import android.graphics.drawable.Drawable;
import app.exteraless.icons.BaseIconPacks;
import org.telegram.messenger.ApplicationLoader;

/** Original Telegram-iOS artwork. Native Resources caches vectors/decoded raster pixels. */
public final class ExactIcons {
    private ExactIcons() {}
    public static boolean isEnabled() { int selected=BaseIconPacks.getSelected(); return selected==BaseIconPacks.BASE_DEFAULT||selected==BaseIconPacks.BASE_CUPERTINO; }

    public static Drawable create(Resources resources,int id,int density,Resources.Theme theme) {
        ExactIconMap.Entry entry=ExactIconMap.get(id);
        if(entry==null||!isEnabled())return null;
        // Source IDs are excluded from the alias map, so this lookup terminates.
        Drawable icon=original(resources,entry.asset,density,theme);
        icon.setTint(entry.color);icon.setAutoMirrored(entry.mirrored);
        return icon;
    }
    private static Drawable original(Resources resources,int asset,int density,Resources.Theme theme) {
        return new OriginalIconDrawable(resources.getDrawableForDensity(asset,density,theme).mutate());
    }
    /** For controls which previously painted approximate paths instead of loading an Android ID. */
    public static Drawable direct(int asset) {
        Context context=ApplicationLoader.applicationContext;
        if(context==null||!isEnabled())return null;
        Drawable icon=original(context.getResources(),asset,0,context.getTheme());
        icon.setTint(0xff000000);
        return icon;
    }
}
