package app.flexygram.icons;

import android.content.res.Resources;
import android.graphics.drawable.Drawable;
import app.exteraless.icons.BaseIconPacks;

/** Compatibility for the former Cupertino selection. It now uses original Telegram artwork. */
public final class CupertinoIcons {
    private CupertinoIcons() {}
    public static Drawable create(Resources resources,int id) {
        if(BaseIconPacks.getSelected()!=BaseIconPacks.BASE_CUPERTINO)return null;
        return ExactIcons.create(resources,id,0,null);
    }
}
