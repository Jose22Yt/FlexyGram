/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.share;
import android.content.Context;
public final class FlexyShareConfig {
    private static Boolean enabled;
    private FlexyShareConfig(){}
    public static boolean enabled(Context c){if(enabled==null)enabled=c.getApplicationContext().getSharedPreferences("flexy_share",0).getBoolean("signature_sheet",false);return enabled;}
    public static void enabled(Context c,boolean value){enabled=value;c.getApplicationContext().getSharedPreferences("flexy_share",0).edit().putBoolean("signature_sheet",value).apply();}
}
