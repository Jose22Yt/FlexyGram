/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Compatibility only: retired home layouts cannot be restored by old preferences/backups. */
public final class HomeStyleConfig {
    public static final String FILE="flexygram_home",STYLE="style";
    public static final int DEFAULT=0;
    private HomeStyleConfig(){}
    public static int normalize(int ignored){return DEFAULT;}
    public static void load(){
        SharedPreferences prefs=ApplicationLoader.applicationContext.getSharedPreferences(FILE,Context.MODE_PRIVATE);
        if(prefs.getInt(STYLE,DEFAULT)!=DEFAULT)prefs.edit().putInt(STYLE,DEFAULT).apply();
    }
}
