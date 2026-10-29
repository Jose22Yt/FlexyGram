/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;
import android.content.Context;
/** Reuses PR117's cached opt-in preference; cancelled tap motion is not read. */
public final class BubbleInteractionSettings {
    private static volatile Boolean panel, bounce, stickers;
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
    /** Separate local animation: never changes the native Telegram motion/navigation engine. */
    public static boolean springBounce(Context context) {
        Boolean value = bounce;
        if (value == null) bounce = value = context.getApplicationContext()
                .getSharedPreferences("flexy_bubble_interaction", 0).getBoolean("spring_bounce", true);
        return value;
    }
    public static void setSpringBounce(Context context, boolean value) {
        bounce = value;
        context.getApplicationContext().getSharedPreferences("flexy_bubble_interaction", 0)
                .edit().putBoolean("spring_bounce", value).apply();
    }
    public static boolean stickerConversion(Context context) {
        Boolean value = stickers;
        if (value == null) stickers = value = context.getApplicationContext()
                .getSharedPreferences("flexy_bubble_interaction", 0).getBoolean("sticker_conversion", true);
        return value;
    }
    public static void setStickerConversion(Context context, boolean value) {
        stickers = value;
        context.getApplicationContext().getSharedPreferences("flexy_bubble_interaction", 0)
                .edit().putBoolean("sticker_conversion", value).apply();
    }

}
