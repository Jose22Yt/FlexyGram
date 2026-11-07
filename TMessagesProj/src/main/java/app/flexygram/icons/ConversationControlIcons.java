/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.icons;

import android.content.Context;
import android.content.res.Resources;
import android.content.res.XmlResourceParser;
import android.graphics.drawable.Drawable;
import java.io.IOException;
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
}
