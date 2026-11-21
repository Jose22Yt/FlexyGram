package tw.nekomimi.nekogram;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Local storage supplied by the isolated Android test host. */
public final class NekoConfig {
    private NekoConfig() {}

    public static SharedPreferences getPreferences() {
        return ApplicationLoader.applicationContext.getSharedPreferences("kyant-test", Context.MODE_PRIVATE);
    }
}
