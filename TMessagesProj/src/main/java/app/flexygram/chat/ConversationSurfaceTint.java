package app.flexygram.chat;

import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.ui.ActionBar.Theme;
import app.flexygram.settings.signature.SettingsCardStyle;

/** Optional 8% theme accent, matching settings cards. Never changes alpha or glass policy. */
public final class ConversationSurfaceTint {
    private static SharedPreferences preferences;
    private static boolean enabled;
    private ConversationSurfaceTint() {}
    private static void load(){
        if(preferences==null && ApplicationLoader.applicationContext!=null){
            preferences=ApplicationLoader.applicationContext.getSharedPreferences("flexy_conversation_surfaces",0);
            enabled=preferences.getBoolean("theme_accent",false);
        }
    }
    public static boolean enabled(){load();return enabled;}
    public static void setEnabled(boolean value){load();if(enabled==value)return;enabled=value;if(preferences!=null)preferences.edit().putBoolean("theme_accent",value).apply();}
    public static int apply(int color,Theme.ResourcesProvider provider){
        if(!enabled())return color;
        return SettingsCardStyle.accentTint(color,Theme.getColor(Theme.key_windowBackgroundWhiteBlueHeader,provider),8);
    }
}
