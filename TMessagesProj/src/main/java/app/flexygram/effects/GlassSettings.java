package app.flexygram.effects;

/** Immutable bounded controls, independent of message-bubble preferences and canceled preview/zone settings. */
public final class GlassSettings {
    public final boolean enabled, fusionAdapt;
    public final int opacity, blur, edge, width, look, materialIntensity, fusion, fusionIntensity, position;
    public GlassSettings(boolean enabled, int opacity, int blur, int edge, int width) {
        this(enabled, opacity, blur, edge, width, 0, 55, 0, 60, true, 5);
    }
    public GlassSettings(boolean enabled, int opacity, int blur, int edge, int width, int look,
                         int materialIntensity, int fusion, int fusionIntensity, boolean fusionAdapt, int position) {
        this.enabled = enabled;
        this.opacity = clamp(opacity, 20, 85);
        this.blur = clamp(blur, 0, 96);
        this.edge = clamp(edge, 0, 200);
        this.width = clamp(width, 0, 60); // tenths of a dp
        this.look = clamp(look, 0, 3);
        this.materialIntensity = clamp(materialIntensity, 0, 100);
        this.fusion = clamp(fusion, 0, 2);
        this.fusionIntensity = clamp(fusionIntensity, 0, 100);
        this.fusionAdapt = fusionAdapt;
        this.position = clamp(position, 1, 5);
    }
    public static GlassSettings defaults() { return new GlassSettings(true, 42, 40, 70, 8); }
    public boolean personalizedContour() { return look != 0 || fusion != 0 || position != 5; }
    public int bubbleStyle() { return look == 1 ? 3 : look == 2 ? 1 : look == 3 ? 2 : 0; }
    public GlassSettings with(int field, int value) {
        return new GlassSettings(field == 0 ? value != 0 : enabled,
                field == 1 ? value : opacity, field == 2 ? value : blur,
                field == 3 ? value : edge, field == 4 ? value : width,
                field == 5 ? value : look, field == 6 ? value : materialIntensity,
                field == 7 ? value : fusion, field == 8 ? value : fusionIntensity,
                field == 9 ? value != 0 : fusionAdapt, field == 10 ? value : position);
    }
    private static int clamp(int value, int min, int max) { return Math.max(min, Math.min(max, value)); }
}
