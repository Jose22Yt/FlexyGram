/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.login;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.utils.ViewOutlineProviderImpl;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.FragmentFloatingButton;

/** Keeps the original done/progress/visibility state machine and native click handler. */
public final class SignatureLoginButton extends FragmentFloatingButton {
    public SignatureLoginButton(Context context) {
        super(context, SignatureLoginPalette.INSTANCE);
        setOutlineProvider(ViewOutlineProviderImpl.boundsWithPaddingRoundRect(0, AndroidUtilities.dp(20)));
        setStateListAnimator(null);
        setTranslationZ(0);
    }
    @Override public void updateColors() {
        super.updateColors();
        StateListDrawable states = new StateListDrawable();
        states.addState(new int[]{-android.R.attr.state_enabled}, surface(SignatureLoginPalette.edge(Theme.isCurrentThemeDark())));
        states.addState(new int[]{android.R.attr.state_pressed}, surface(SignatureLoginPalette.color(Theme.key_chats_actionPressedBackground)));
        states.addState(new int[]{}, surface(SignatureLoginPalette.color(Theme.key_chats_actionBackground)));
        setBackground(states);
    }
    private GradientDrawable surface(int color) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(color); shape.setCornerRadius(AndroidUtilities.dp(20)); return shape;
    }
}
