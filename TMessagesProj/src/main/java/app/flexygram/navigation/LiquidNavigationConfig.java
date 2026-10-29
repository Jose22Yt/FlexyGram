/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Bottom Bar settings. Legacy class/store names preserve existing preferences, not Liquid effects.
 * Reads are cached; drawing never reads disk. Previous full destination order remains recoverable.
 */
public final class LiquidNavigationConfig {
    private static final String NAME="flexy_liquid_navigation";
    private static boolean loaded,labels=true,animate=true;
    private static int compaction;
    private static int[] order=LiquidNavigationDestinations.defaults();
    public enum Parameter {
        HEIGHT(33), COMPACT(50), WIDTH(100), ICON(50), LABEL_GAP(35), INNER_MARGIN(25),
        BOTTOM_GAP(25), SIDE_GAP(30), RADIUS(75), SPEED(50), DAMPING(76);
        final int initial; int value;
        Parameter(int initial){this.initial=initial;value=initial;}
    }
    private LiquidNavigationConfig(){}
    private static SharedPreferences prefs(){return ApplicationLoader.applicationContext.getSharedPreferences(NAME,Context.MODE_PRIVATE);}
    private static int clamp(int n){return Math.max(0,Math.min(100,n));}
    public static void load(){
        if(loaded)return;
        SharedPreferences p=prefs();
        labels=p.getBoolean("labels",true);animate=p.getBoolean("bottom_animation",true);
        compaction=Math.max(0,Math.min(3,p.getInt("bottom_compaction",0)));
        for(Parameter v:Parameter.values())v.value=clamp(p.getInt(v.name().toLowerCase(java.util.Locale.ROOT),v.initial));
        int[] previous=parse(p.getString("destinations","0,1,2,4"));
        order=LiquidNavigationDestinations.sanitize(previous);
        if(!p.getBoolean("bottom_schema1",false)){
            SharedPreferences.Editor migration=p.edit().putBoolean("bottom_schema1",true);
            // Do not destroy the old >6 order. It can be restored/exported independently.
            migration.putString("bottom_previous_destinations",p.getString("destinations","0,1,2,4"));
            migration.putString("destinations",encode(order));
            int old=p.getInt("compaction",0);compaction=old==1?1:old==2?2:old==4?3:0;
            migration.putInt("bottom_compaction",compaction).apply();
        }
        loaded=true;
    }
    private static int[] parse(String raw){String[] parts=raw.split(",");int[] ids=new int[Math.min(parts.length,64)];for(int i=0;i<ids.length;i++)try{ids[i]=Integer.parseInt(parts[i]);}catch(NumberFormatException e){ids[i]=-1;}return ids;}
    private static String encode(int[] ids){StringBuilder s=new StringBuilder();for(int id:ids){if(s.length()>0)s.append(',');s.append(id);}return s.toString();}
    public static boolean configured(){load();return true;}
    public static int value(Parameter p){load();return p.value;}
    public static void value(Parameter p,int v){load();p.value=clamp(v);prefs().edit().putInt(p.name().toLowerCase(java.util.Locale.ROOT),p.value).apply();}
    public static boolean labels(){load();return labels;}
    public static void labels(boolean v){load();labels=v;prefs().edit().putBoolean("labels",v).apply();}
    public static boolean animation(){load();return animate;}
    public static void animation(boolean v){load();animate=v;prefs().edit().putBoolean("bottom_animation",v).apply();}
    public static int[] order(){load();return order.clone();}
    public static void order(int[] ids){load();order=LiquidNavigationDestinations.sanitize(ids);prefs().edit().putString("destinations",encode(order)).apply();}
    public static int[] previousOrder(){load();return parse(prefs().getString("bottom_previous_destinations","0,1,2,4"));}
    public static int[] shown(int slots){return LiquidNavigationDestinations.fit(order(),slots);}
    public static int compaction(){load();return compaction;}
    public static void compaction(int v){load();compaction=Math.max(0,Math.min(3,v));prefs().edit().putInt("bottom_compaction",compaction).apply();}
    public static boolean hideLabels(int count,int availableDp){return !labels()||compaction()==2||availableDp/Math.max(1,count)<60;}
    public static int heightDp(){return compaction()==3?48+Math.round(value(Parameter.HEIGHT)*.32f):compaction()==2?48:compaction()==1?54:60;}
    public static int innerMarginDp(){return value(Parameter.INNER_MARGIN)*8/100;}
    public static int bottomGapDp(){return 4+value(Parameter.BOTTOM_GAP)*20/100;}
    public static int sideGapDp(){return 4+value(Parameter.SIDE_GAP)*20/100;}
    public static int labelGapDp(){return 1+value(Parameter.LABEL_GAP)*5/100;}
    public static int iconDp(){return 18+value(Parameter.ICON)*10/100;}
    public static float widthFraction(){return .70f+value(Parameter.WIDTH)*.003f;}
    public static float radiusDp(){return Math.min(heightDp()/2f,8+value(Parameter.RADIUS)*.28f);}
    public static float damping(){return .85f+value(Parameter.DAMPING)*.0015f;}
    public static float stiffness(){return 300f+value(Parameter.SPEED)*7f;}
    public static int contentPaddingDp(){return compaction()==3?value(Parameter.COMPACT)*4/100:compaction()==0?3:compaction()==1?2:0;}
    public static void reset(){
        // Preserve the recoverable pre-migration order even when restoring defaults.
        SharedPreferences.Editor e=prefs().edit();for(Parameter p:Parameter.values())e.remove(p.name().toLowerCase(java.util.Locale.ROOT));
        e.putBoolean("labels",true).putBoolean("bottom_animation",true).putInt("bottom_compaction",0).putString("destinations",encode(LiquidNavigationDestinations.defaults())).apply();loaded=false;load();
    }
}
