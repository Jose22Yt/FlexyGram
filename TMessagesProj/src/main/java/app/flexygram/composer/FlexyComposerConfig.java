package app.flexygram.composer;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Separate local presentation preferences. No account, transport or draft data. */
public final class FlexyComposerConfig {
    public static final String STYLE = "style";
    public static final String GLASS = "pearlGlass";
    public static final int CLASSIC = 0;
    public static final int COMPACT_IOS = 1;

    private FlexyComposerConfig() { }

    public static SharedPreferences preferences() {
        return ApplicationLoader.applicationContext.getSharedPreferences("flexygram_composer", Context.MODE_PRIVATE);
    }
    public static boolean compact() { return preferences().getInt(STYLE, CLASSIC) == COMPACT_IOS; }
    public static boolean glass() { return preferences().getBoolean(GLASS, false); }
    public static void setStyle(int value) {
        if (value != CLASSIC && value != COMPACT_IOS) throw new IllegalArgumentException("Unknown composer style");
        preferences().edit().putInt(STYLE, value).apply();
    }
    public static void setGlass(boolean value) { preferences().edit().putBoolean(GLASS, value).apply(); }
}
