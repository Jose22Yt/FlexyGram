/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.login;

import android.content.Context;
import android.widget.ImageView;
import org.telegram.messenger.R;

/** Shared Work1 resource contract: no duplicate launcher artwork or alias changes. */
public final class SignatureIdentity {
    public static boolean applyPlane(ImageView image) {
        Context context = image.getContext();
        int shared = context.getResources().getIdentifier("ic_flexy_blue", "mipmap", context.getPackageName());
        image.setImageResource(shared != 0 ? shared : R.drawable.msg_send);
        if (shared == 0) image.setColorFilter(SignatureLoginPalette.accent(org.telegram.ui.ActionBar.Theme.isCurrentThemeDark()));
        else image.clearColorFilter();
        return shared != 0;
    }
}
