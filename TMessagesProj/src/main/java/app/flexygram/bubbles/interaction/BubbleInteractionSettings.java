/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;
import android.content.Context;
/** Reuses PR117's cached opt-in preference; cancelled tap motion is not read. */
public final class BubbleInteractionSettings {
    private static volatile Boolean panel;
    private BubbleInteractionSettings() {}
    public static boolean signaturePanel(Context context) {
        Boolean value=panel;
        if(value==null)panel=value=context.getApplicationContext().getSharedPreferences("flexy_bubble_interaction",0).getBoolean("signature_panel",false);
        return value;
    }
    public static void setSignaturePanel(Context context,boolean value) {
        panel=value;
        context.getApplicationContext().getSharedPreferences("flexy_bubble_interaction",0).edit().putBoolean("signature_panel",value).apply();
    }
}
