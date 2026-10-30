/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Fixed compact Home profile. Legacy store name is used solely for one-time migration.
 * No user-controlled geometry, opacity, tab order or motion survives into rendering.
 */
public final class LiquidNavigationConfig {
    private static boolean migrated;
    private LiquidNavigationConfig() {}
    public static void load() {
        if (migrated || ApplicationLoader.applicationContext == null) return;
        SharedPreferences p=ApplicationLoader.applicationContext.getSharedPreferences("flexy_liquid_navigation",0);
        if (!p.getBoolean("home_defaults_v2",false)) {
            SharedPreferences.Editor edit=p.edit();
            String[] retired={"height","compact","width","icon","label_gap","inner_margin",
                    "bottom_gap","side_gap","radius","speed","damping","labels","bottom_animation",
                    "bottom_compaction","compaction","destinations","enabled","opacity","intensity"};
            for (String key:retired) edit.remove(key);
            // These legacy switches can hide/float the entire Home surface.
            xyz.nextalone.nagram.NaConfig.INSTANCE.getHideBottomNavigationBar().setConfigBool(false);
            tw.nekomimi.nekogram.NekoConfig.getPreferences().edit()
                    .remove("OEAppearanceBottomNavigationFloating").apply();
            edit.putBoolean("home_defaults_v2",true).apply();
        }
        migrated=true;
    }
    public static boolean configured(){load();return true;}
    public static boolean labels(){return true;}
    public static boolean animation(){return true;}
    public static int[] order(){return LiquidNavigationDestinations.defaults();}
    public static int[] shown(int slots){return LiquidNavigationDestinations.fit(order(),slots);}
    public static boolean hideLabels(int count,int availableDp){return availableDp/Math.max(1,count)<60;}
    public static int heightDp(){return 60;}
    public static int innerMarginDp(){return 2;}
    public static int bottomGapDp(){return 9;}
    public static int sideGapDp(){return 10;}
    public static int labelGapDp(){return 2;}
    public static int iconDp(){return 23;}
    public static float widthFraction(){return 1f;}
    public static float radiusDp(){return 29f;}
    public static float damping(){return .964f;}
    public static float stiffness(){return 650f;}
    public static int contentPaddingDp(){return 3;}
}
