/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.icons;

import android.content.Context;
import android.content.res.Resources;
import android.content.res.XmlResourceParser;
import android.graphics.drawable.Drawable;
import android.util.TypedValue;
import java.io.IOException;
import java.io.InputStream;
import org.xmlpull.v1.XmlPullParserException;

/** Fixed conversation glyphs: decode the packaged vector, bypassing optional icon-pack substitution. */
public final class ConversationControlIcons {
    private ConversationControlIcons() { }

    public static Drawable load(Context context, int resource) {
        Resources resources = context.getResources();
        try (XmlResourceParser parser = resources.getXml(resource)) {
            return Drawable.createFromXml(resources, parser, context.getTheme());
        } catch (IOException | XmlPullParserException error) {
            throw new Resources.NotFoundException("Invalid conversation control vector", error);
        }
    }

    /** Decode the original packaged bitmap, keeping density and bypassing icon packs. */
    public static Drawable loadBitmap(Context context, int resource) {
        Resources resources = context.getResources();
        TypedValue value = new TypedValue();
        try (InputStream stream = resources.openRawResource(resource, value)) {
            Drawable icon = Drawable.createFromResourceStream(resources, value, stream, null);
            if (icon == null) throw new Resources.NotFoundException("Invalid conversation control bitmap");
            return icon;
        } catch (IOException error) {
            throw new Resources.NotFoundException("Invalid conversation control bitmap", error);
        }
    }
}
