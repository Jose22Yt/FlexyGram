package app.flexygram.effects;

/** Immutable, bounded editor snapshot; a draft never changes the running application. */
public final class GlassSettings {
    public static final int ALL_ZONES = 127;
    private static final int[][] PRESETS = {{80, 12, 25, 6, 0}, {65, 24, 40, 10, 1}, {50, 40, 65, 15, 2}};
    public final boolean enabled;
    public final int opacity, blur, edge, width, style, color, zones;

    public GlassSettings(boolean enabled, int opacity, int blur, int edge, int width, int style, int color, int zones) {
        this.enabled = enabled;
        this.opacity = clamp(opacity, 20, 100);
        this.blur = clamp(blur, 0, 48);
        this.edge = clamp(edge, 0, 100);
        this.width = clamp(width, 0, 30); // tenths of a dp
        this.style = clamp(style, 0, 2);
        this.color = color;
        this.zones = zones & ALL_ZONES;
    }
    public static GlassSettings defaults() { return new GlassSettings(true, 65, 24, 40, 10, 1, 0, ALL_ZONES); }
    public GlassSettings with(int field, int value) {
        return new GlassSettings(field == 0 ? value != 0 : enabled,
                field == 1 ? value : opacity, field == 2 ? value : blur, field == 3 ? value : edge,
                field == 4 ? value : width, field == 5 ? value : style, field == 6 ? value : color,
                field == 7 ? value : zones);
    }
    public GlassSettings preset(int index) {
        int[] p = PRESETS[index >= 0 && index < PRESETS.length ? index : 1];
        return new GlassSettings(enabled, p[0], p[1], p[2], p[3], p[4], color, zones);
    }
    public int presetIndex() {
        for (int i = 0; i < PRESETS.length; i++) {
            int[] p = PRESETS[i];
            if (opacity == p[0] && blur == p[1] && edge == p[2] && width == p[3] && style == p[4]) return i;
        }
        return -1;
    }
    public static int clamp(int value, int min, int max) { return Math.max(min, Math.min(max, value)); }
}
