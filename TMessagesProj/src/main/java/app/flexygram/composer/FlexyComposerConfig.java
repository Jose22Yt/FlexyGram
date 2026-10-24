package app.flexygram.composer;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/** Separate local presentation preferences. No account, transport or draft data. */
public final class FlexyComposerConfig {
    public static final String STYLE = "style";
    public static final String GLASS = "pearlGlass";
    public static final String POSITION = "verticalPosition";
    public static final String LEVEL = "compactLevel";
    public static final String ICONS = "iconAppearance";
    public static final String GAP = "componentGap";
    public static final int CLASSIC = 0;
    public static final int COMPACT_IOS = 1;

    private FlexyComposerConfig() { }

    public static SharedPreferences preferences() {
        return ApplicationLoader.applicationContext.getSharedPreferences("flexygram_composer", Context.MODE_PRIVATE);
    }
    public static boolean compact() { return preferences().getInt(STYLE, CLASSIC) == COMPACT_IOS; }
    public static boolean referenceIcons() { return preferences().getInt(ICONS, 0) != 1; }
    public static void setReferenceIcons(boolean reference) { preferences().edit().putInt(ICONS, reference ? 0 : 1).apply(); }
    public static boolean glass() { return preferences().getBoolean(GLASS, false); }
    public static int position() { return ComposerStyle.position(preferences().getInt(POSITION, 0)); }
    public static int level() { return ComposerStyle.level(preferences().getInt(LEVEL, 0)); }
    public static int gap() { return ComposerStyle.gap(level(), preferences().getInt(GAP, 0)); }
    public static void setPosition(int value) { if (position() == ComposerStyle.position(value)) return; preferences().edit().putInt(POSITION, ComposerStyle.position(value)).apply(); }
    public static void setLevel(int value) { preferences().edit().putInt(LEVEL, ComposerStyle.level(value)).apply(); }
    public static void setGap(int value) { preferences().edit().putInt(GAP, ComposerStyle.clamp(value, ComposerStyle.MIN_GAP, ComposerStyle.MAX_GAP)).apply(); }
    public static void reset() {
        preferences().edit().putInt(STYLE, COMPACT_IOS).putBoolean(GLASS, true)
            .remove(ICONS).remove(POSITION).remove(LEVEL).remove(GAP).apply();
    }
    public static void setStyle(int value) {
        if (value != CLASSIC && value != COMPACT_IOS) throw new IllegalArgumentException("Unknown composer style");
        preferences().edit().putInt(STYLE, value).apply();
    }
    public static void setGlass(boolean value) { preferences().edit().putBoolean(GLASS, value).apply(); }
}
