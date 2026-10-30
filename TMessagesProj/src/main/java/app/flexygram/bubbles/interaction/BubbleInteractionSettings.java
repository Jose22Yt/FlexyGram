/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;
import android.content.Context;
/** Reuses PR117's cached opt-in preference; cancelled tap motion is not read. */
public final class BubbleInteractionSettings {
    private static volatile Boolean panel, bounce, tap, tapPanel;
    private static int compression=-1,rebound=-1,recovery=-1;
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

    private static android.content.SharedPreferences prefs(Context c){return c.getApplicationContext().getSharedPreferences("flexy_bubble_interaction",0);}
    public static boolean tapAnimation(Context c){if(tap==null)tap=prefs(c).getBoolean("tap_animation",true);return tap;}
    public static void tapAnimation(Context c,boolean v){tap=v;prefs(c).edit().putBoolean("tap_animation",v).apply();}
    public static boolean tapPanel(Context c){if(tapPanel==null)tapPanel=prefs(c).getBoolean("tap_panel",true);return tapPanel;}
    public static void tapPanel(Context c,boolean v){tapPanel=v;prefs(c).edit().putBoolean("tap_panel",v).apply();}
    public static int compression(Context c){if(compression<0)compression=bounded(prefs(c).getInt("tap_compression",55));return compression;}
    public static int rebound(Context c){if(rebound<0)rebound=bounded(prefs(c).getInt("tap_rebound",45));return rebound;}
    public static int recovery(Context c){if(recovery<0)recovery=bounded(prefs(c).getInt("tap_recovery",55));return recovery;}
    public static void parameter(Context c,int which,int value){value=bounded(value);if(which==0)compression=value;else if(which==1)rebound=value;else recovery=value;prefs(c).edit().putInt(which==0?"tap_compression":which==1?"tap_rebound":"tap_recovery",value).apply();}
    private static int bounded(int v){return Math.max(0,Math.min(100,v));}
    public static void resetTap(Context c){tap=true;tapPanel=true;compression=55;rebound=45;recovery=55;prefs(c).edit().putBoolean("tap_animation",true).putBoolean("tap_panel",true).putInt("tap_compression",55).putInt("tap_rebound",45).putInt("tap_recovery",55).apply();}
}
