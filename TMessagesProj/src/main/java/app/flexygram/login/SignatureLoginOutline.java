/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.login;

import android.content.Context;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.OutlineTextContainerView;

/** Native focus/error/label springs and attached edit text, with an opt-in Matte surface. */
public final class SignatureLoginOutline extends OutlineTextContainerView {
    public SignatureLoginOutline(Context context) {
        super(context, SignatureLoginPalette.INSTANCE);
        setCornerRadius(AndroidUtilities.dp(16));
        updateColor();
    }
    @Override public void updateColor() {
        super.updateColor();
        setSignatureSurfaceColor(SignatureLoginPalette.surface(Theme.isCurrentThemeDark()));
    }
}
