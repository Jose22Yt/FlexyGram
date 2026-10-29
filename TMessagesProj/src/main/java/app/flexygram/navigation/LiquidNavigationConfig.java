/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Cached UI-thread preferences; drawing performs no SharedPreferences lookup. */
public final class LiquidNavigationConfig {
    private static final String NAME="flexy_liquid_navigation";
    private static boolean loaded,configured,enabled,labels=true;
    private static int[] order=LiquidNavigationDestinations.defaults();
    public enum Parameter {
        OPACITY(55), ELASTICITY(65), DEFORMATION(65), SPEED(50), DAMPING(76),
        REBOUND(30), FOLLOW(100), SETTLE(50), HEIGHT(0), COMPACT(50), SPACING(50), ICON(50), WIDTH(100);
        final int initial; int value;
        Parameter(int initial){this.initial=initial;this.value=initial;}
    }
    private LiquidNavigationConfig(){}
    private static SharedPreferences prefs(){return ApplicationLoader.applicationContext.getSharedPreferences(NAME,Context.MODE_PRIVATE);}
    public static void load(){
        if(loaded)return;
        SharedPreferences p=prefs();configured=p.getBoolean("configured",false);
        enabled=p.getBoolean("drag_indicator",false);labels=p.getBoolean("labels",true);
        for(Parameter v:Parameter.values())v.value=LiquidNavigationMath.clampPercent(p.getInt(v.name().toLowerCase(java.util.Locale.ROOT),v.initial));
        String[] raw=p.getString("destinations","0,1,2,4").split(",");int[] ids=new int[Math.min(raw.length,64)];
        for(int i=0;i<ids.length;i++){try{ids[i]=Integer.parseInt(raw[i]);}catch(NumberFormatException e){ids[i]=-1;}}
        order=LiquidNavigationDestinations.sanitize(ids);loaded=true;
    }
    public static boolean configured(){load();return configured;}
    public static boolean enabled(){load();return enabled;}
    public static void enabled(boolean v){load();enabled=v;configured=true;prefs().edit().putBoolean("drag_indicator",v).putBoolean("configured",true).apply();}
    public static int value(Parameter p){load();return p.value;}
    public static void value(Parameter p,int v){load();p.value=LiquidNavigationMath.clampPercent(v);configured=true;prefs().edit().putInt(p.name().toLowerCase(java.util.Locale.ROOT),p.value).putBoolean("configured",true).apply();}
    public static float elasticity(){return value(Parameter.ELASTICITY)/100f;}
    public static void elasticity(int v){value(Parameter.ELASTICITY,v);}
    public static int opacity(){return value(Parameter.OPACITY);}
    public static void opacity(int v){value(Parameter.OPACITY,v);}
    public static boolean labels(){load();return labels;}
    public static void labels(boolean v){load();labels=v;configured=true;prefs().edit().putBoolean("labels",v).putBoolean("configured",true).apply();}
    public static int[] order(){load();return order.clone();}
    public static void order(int[] ids){load();order=LiquidNavigationDestinations.sanitize(ids);configured=true;StringBuilder s=new StringBuilder();for(int id:order){if(s.length()>0)s.append(',');s.append(id);}prefs().edit().putString("destinations",s.toString()).putBoolean("configured",true).apply();}
    public static int heightDp(){return 60+value(Parameter.HEIGHT)*24/100;}
    public static int iconDp(){return 18+value(Parameter.ICON)*10/100;}
    public static int spacingDp(){return 4+value(Parameter.SPACING)*8/100;}
    public static float damping(){return .65f+value(Parameter.DAMPING)*.0034f;}
    public static float stiffness(){return 240f+value(Parameter.SPEED)*6f;}
    public static long settleMillis(){return 160L+value(Parameter.SETTLE)*3L;}
    public static void reset(){loaded=false;prefs().edit().clear().apply();load();order(LiquidNavigationDestinations.defaults());}
}
