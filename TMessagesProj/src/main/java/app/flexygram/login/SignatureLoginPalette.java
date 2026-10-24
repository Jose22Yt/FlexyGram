/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.login;

import org.telegram.messenger.BuildConfig;
import org.telegram.ui.ActionBar.Theme;

/** Login-scoped colors. Never writes the global theme or any preference. */
public final class SignatureLoginPalette implements Theme.ResourcesProvider {
    public static final SignatureLoginPalette INSTANCE = new SignatureLoginPalette();
    public static boolean enabled() { return BuildConfig.CONNECTED_ALPHA; }
    public static int background(boolean dark) { return dark ? 0xFF11151C : 0xFFF7F8FA; }
    public static int surface(boolean dark) { return dark ? 0xFF1C222D : 0xFFFFFFFF; }
    public static int ink(boolean dark) { return dark ? 0xFFF0F2F6 : 0xFF252C38; }
    public static int secondary(boolean dark) { return dark ? 0xFFABB6C7 : 0xFF606D80; }
    public static int accent(boolean dark) { return dark ? 0xFF63ACFF : 0xFF1767C4; }
    public static int edge(boolean dark) { return dark ? 0xFF536176 : 0xFFAAB6C6; }
    @Override public int getColor(int key) { return color(key); }
    public static int color(int key) { return color(key, null); }
    public static int color(int key, boolean[] isDefault, boolean ignoreAnimation) {
        if (!enabled()) return Theme.getColor(key, isDefault, ignoreAnimation);
        if (isDefault != null) isDefault[0] = false;
        return color(key);
    }
    public static int color(int key, Theme.ResourcesProvider fallback) {
        if (!enabled()) return Theme.getColor(key, fallback);
        boolean dark = Theme.isCurrentThemeDark();
        if (key == Theme.key_windowBackgroundWhite || key == Theme.key_dialogBackground) return background(dark);
        if (key == Theme.key_windowBackgroundWhiteBlackText || key == Theme.key_dialogTextBlack) return ink(dark);
        if (key == Theme.key_windowBackgroundWhiteGrayText || key == Theme.key_windowBackgroundWhiteGrayText6 ||
            key == Theme.key_windowBackgroundWhiteHintText || key == Theme.key_dialogTextGray2) return secondary(dark);
        if (key == Theme.key_windowBackgroundWhiteInputField) return edge(dark);
        if (key == Theme.key_dialogTopBackground) return surface(dark);
        if (key == Theme.key_listSelector) return dark ? 0x1F63ACFF : 0x141767C4;
        if (key == Theme.key_login_progressInner) return dark ? 0xFF233247 : 0xFFDBE8F7;
        if (key == Theme.key_login_progressOuter || key == Theme.key_changephoneinfo_image2 || key == Theme.key_windowBackgroundWhiteBlueText2 || key == Theme.key_windowBackgroundWhiteInputFieldActivated || key == Theme.key_windowBackgroundWhiteValueText ||
            key == Theme.key_windowBackgroundWhiteBlueText4 || key == Theme.key_windowBackgroundWhiteLinkText ||
            key == Theme.key_chat_messageLinkIn || key == Theme.key_chats_actionBackground ||
            key == Theme.key_featuredStickers_addButton || key == Theme.key_checkboxSquareBackground) return accent(dark);
        if (key == Theme.key_chats_actionIcon || key == Theme.key_checkboxSquareCheck) return dark ? 0xFF11151C : 0xFFFFFFFF;
        if (key == Theme.key_featuredStickers_addButtonPressed || key == Theme.key_chats_actionPressedBackground) return dark ? 0xFF8EC4FF : 0xFF12539E;
        // Errors, warnings, verification states and all unknown keys keep native semantics.
        return Theme.getColor(key);
    }
}
