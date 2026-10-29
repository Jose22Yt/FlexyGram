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
        OPACITY(70), REFLECTION(65), OUTLINE(65), INTENSITY(80), LENS_SIZE(60), ELASTICITY(65), DEFORMATION(65), SPEED(50), DAMPING(76),
        REBOUND(30), FOLLOW(100), SETTLE(50), HEIGHT(0), COMPACT(50), SPACING(50), ICON(50), WIDTH(100);
        final int initial; int value;
        Parameter(int initial){this.initial=initial;this.value=initial;}
    }
    public enum Profile { FLUID, SIGNATURE, MINIMAL }
    public static void profile(Profile profile) {
        load();
        int[] appearance = profile == Profile.MINIMAL ? new int[]{85,25,35,45,45}
                : profile == Profile.FLUID ? new int[]{75,45,50,65,55} : new int[]{70,65,65,80,60};
        Parameter[] names = {Parameter.OPACITY,Parameter.REFLECTION,Parameter.OUTLINE,Parameter.INTENSITY,Parameter.LENS_SIZE};
        SharedPreferences.Editor editor=prefs().edit();
        for(int i=0;i<names.length;i++){
            names[i].value=appearance[i];editor.putInt(names[i].name().toLowerCase(java.util.Locale.ROOT),appearance[i]);
        }
        Parameter[] motion={Parameter.ELASTICITY,Parameter.DEFORMATION,Parameter.SPEED,Parameter.DAMPING,Parameter.REBOUND,Parameter.FOLLOW,Parameter.SETTLE};
        int[] values=profile==Profile.MINIMAL?new int[]{25,25,85,95,0,100,15}
                :profile==Profile.FLUID?new int[]{55,55,65,85,15,100,35}:new int[]{80,80,60,76,35,100,45};
        for(int i=0;i<motion.length;i++){
            motion[i].value=values[i];editor.putInt(motion[i].name().toLowerCase(java.util.Locale.ROOT),values[i]);
        }
        configured=true;editor.putBoolean("configured",true).apply();
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
