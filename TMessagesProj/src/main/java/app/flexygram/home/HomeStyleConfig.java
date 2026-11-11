/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** UI-thread snapshot. Account-local folder references are deliberately excluded from portable exports. */
public final class HomeStyleConfig {
    public static final String FILE="flexygram_home",STYLE="style";
    public static final int DEFAULT=0,IOS=2;
    private static int style;
    private static boolean loaded;
    private HomeStyleConfig(){}
    private static SharedPreferences prefs(){return ApplicationLoader.applicationContext.getSharedPreferences(FILE,Context.MODE_PRIVATE);}
    public static int normalize(int value){return value==IOS?IOS:DEFAULT;}
    public static void load(){
        int stored=prefs().getInt(STYLE,DEFAULT);
        style=normalize(stored);loaded=true;
        // Retired Essential layout never silently turns into the new iPhone style.
        if(stored!=style)prefs().edit().putInt(STYLE,style).apply();
    }
    public static int style(){if(!loaded)load();return style;}
    public static boolean isIos(){return style()==IOS;}
    public static int optionStyle(int option){return option==1?IOS:DEFAULT;}
    public static void setStyle(int value){loaded=true;style=normalize(value);prefs().edit().putInt(STYLE,style).apply();}
    /** Official ChatListNavigationBar: 3 + 44 + 9 pt; search scroll distance 54 pt. */
    public static int headerDp(){return 56;}
    public static int extraHeaderDp(boolean enabled){return enabled?54:0;}
}
