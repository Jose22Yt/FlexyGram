/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.login;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.InsetDrawable;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.OutlineTextContainerView;

/** Native focus/error/label springs and attached edit text, with an opt-in Matte surface. */
public final class SignatureLoginOutline extends OutlineTextContainerView {
    private GradientDrawable surface;
    public SignatureLoginOutline(Context context) {
        super(context, SignatureLoginPalette.INSTANCE);
        setCornerRadius(AndroidUtilities.dp(16));
        surface = new GradientDrawable();
        surface.setCornerRadius(AndroidUtilities.dp(16));
        setBackground(new InsetDrawable(surface, 0, AndroidUtilities.dp(6), 0, 0));
        updateColor();
    }
    @Override public void updateColor() {
        super.updateColor();
        if (surface != null) surface.setColor(SignatureLoginPalette.surface(Theme.isCurrentThemeDark()));
    }
}
