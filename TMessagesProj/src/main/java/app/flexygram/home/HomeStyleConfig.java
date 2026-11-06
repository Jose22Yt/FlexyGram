/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** UI-thread snapshot. Account-local folder references are deliberately excluded from portable exports. */
public final class HomeStyleConfig {
    public static final String FILE="flexygram_home",STYLE="style";
    public static final int DEFAULT=0,ESSENTIALS=1;
    private static int style;
    private HomeStyleConfig(){}
    private static SharedPreferences prefs(){return ApplicationLoader.applicationContext.getSharedPreferences(FILE,Context.MODE_PRIVATE);}
    public static int normalize(int value){return value==ESSENTIALS?ESSENTIALS:DEFAULT;}
    public static void load(){style=normalize(prefs().getInt(STYLE,DEFAULT));}
    public static int style(){return style;}
    public static void setStyle(int value){style=normalize(value);prefs().edit().putInt(STYLE,style).apply();}
    public static int favoriteFolder(int account){return prefs().getInt("favorite_folder_"+account,0);}
    public static void favoriteFolder(int account,int id){if(id>1)prefs().edit().putInt("favorite_folder_"+account,id).apply();}
    public static int extraHeaderDp(boolean enabled){return enabled?128:0;}
}
