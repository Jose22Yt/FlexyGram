package app.flexygram.kyant;

import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Independent, default-off home dock material. Reads the existing choice without reviving bounce. */
public final class KyantDockConfig {
    private static SharedPreferences preferences;
    private static boolean enabled;
    private KyantDockConfig() {}
    private static void load() {
        if(preferences==null && ApplicationLoader.applicationContext!=null){
            // Keep the installed user's dock choice; the removed elastic key is never read.
            preferences=ApplicationLoader.applicationContext.getSharedPreferences("flexy_elastic_interaction",0);
            enabled=preferences.getBoolean("kyant_home_dock",false);
        }
    }
    public static void reload(){load();if(preferences!=null)enabled=preferences.getBoolean("kyant_home_dock",false);}
    public static boolean enabled(){load();return enabled;}
    public static void setEnabled(boolean value){load();enabled=value;if(preferences!=null)preferences.edit().putBoolean("kyant_home_dock",value).apply();}
}
