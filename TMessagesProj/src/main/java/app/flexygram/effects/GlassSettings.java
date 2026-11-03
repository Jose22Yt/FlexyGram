package app.flexygram.effects;

/** Bounded immutable material values. No preview state or selectable application zones. */
public final class GlassSettings {
    public final boolean enabled;
    public final int opacity, blur, edge, width;
    public GlassSettings(boolean enabled, int opacity, int blur, int edge, int width) {
        this.enabled = enabled;
        this.opacity = clamp(opacity, 20, 85);
        this.blur = clamp(blur, 0, 48);
        this.edge = clamp(edge, 0, 100);
        this.width = clamp(width, 0, 30); // tenths of a dp
    }
    public static GlassSettings defaults() { return new GlassSettings(true, 42, 40, 70, 8); }
    public GlassSettings with(int field, int value) {
        return new GlassSettings(field == 0 ? value != 0 : enabled,
                field == 1 ? value : opacity, field == 2 ? value : blur,
                field == 3 ? value : edge, field == 4 ? value : width);
    }
    private static int clamp(int value, int min, int max) { return Math.max(min, Math.min(max, value)); }
}
