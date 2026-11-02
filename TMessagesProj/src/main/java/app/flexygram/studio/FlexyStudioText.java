/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;
import org.telegram.messenger.R;
/** Stable identifiers are never translated; only the presentation is localized. */
public final class FlexyStudioText {
    private FlexyStudioText(){}
    public static int section(String id) {
        switch(id){case "bubbles":return R.string.FlexyStudioBubbles;case "header":return R.string.FlexyStudioHeader;
            case "composer":return R.string.FlexyStudioComposer;case "icon":return R.string.FlexyStudioIcon;default:throw new IllegalArgumentException("section");}
    }
    public static int icon(String id) {
        switch(id){case "bubbles":return R.drawable.msg_discussion;case "header":return R.drawable.msg_contacts;
            case "composer":return R.drawable.msg_edit;case "icon":return R.drawable.msg_theme;default:throw new IllegalArgumentException("section");}
    }
}
