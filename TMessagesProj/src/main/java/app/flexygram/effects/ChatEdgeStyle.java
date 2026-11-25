package app.flexygram.effects;

import tw.nekomimi.nekogram.NekoConfig;

/** The selected contour treatment for the conversation controls. */
public final class ChatEdgeStyle {
    static final int CURRENT = 0;
    static final int REFLECTION = 1;
    static final int SUBTLE = 2;
    static final int SATIN = 3;
    static final int COLOROS_GLASS = 4;

    private static final String LEGACY_KEY = "flexyChatEdgeReflection";
    private static final String KEY = "flexyChatEdgeStyle";
    private static int selected = readStyle();

    private ChatEdgeStyle() {}

    private static int readStyle() {
        final var preferences = NekoConfig.getPreferences();
        return normalize(preferences.getInt(KEY, preferences.getBoolean(LEGACY_KEY, false)
                ? REFLECTION : CURRENT));
    }

    private static int normalize(int style) {
        return style >= CURRENT && style <= COLOROS_GLASS ? style : CURRENT;
    }

    static int getSelected() {
        return selected;
    }

    public static boolean hasCustomEdge() {
        return selected != CURRENT;
    }

    public static boolean isSubtle() {
        return selected == SUBTLE;
    }

    public static boolean isSatin() {
        return selected == SATIN;
    }

    public static boolean isColorOsGlass() {
        return selected == COLOROS_GLASS;
    }

    public static boolean isGlobalSurfaceEdge() {
        return selected == SATIN || selected == COLOROS_GLASS;
    }

    public static ChatEdgeReflection updateReflection(ChatEdgeReflection reflection) {
        if (reflection == null) reflection = new ChatEdgeReflection();
        reflection.setSubtle(isSubtle());
        reflection.setSatin(isSatin());
        reflection.setColorOsGlass(isColorOsGlass());
        return reflection;
    }

    static void setSelected(int style) {
        style = normalize(style);
        if (selected == style) return;
        selected = style;
        NekoConfig.getPreferences().edit().putInt(KEY, style).apply();
    }
}
