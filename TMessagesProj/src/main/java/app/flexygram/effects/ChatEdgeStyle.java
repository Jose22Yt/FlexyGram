package app.flexygram.effects;

import tw.nekomimi.nekogram.NekoConfig;

/** One local choice for the edges of chat controls. */
public final class ChatEdgeStyle {
    private static final String KEY = "flexyChatEdgeReflection";
    private static boolean reflective = NekoConfig.getPreferences().getBoolean(KEY, false);

    private ChatEdgeStyle() {}

    public static boolean isReflective() {
        return reflective;
    }

    public static void setReflective(boolean value) {
        if (reflective == value) return;
        reflective = value;
        NekoConfig.getPreferences().edit().putBoolean(KEY, value).apply();
    }
}
