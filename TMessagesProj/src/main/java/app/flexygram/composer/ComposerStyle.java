package app.flexygram.composer;

/** Bounded presentation policy. Native 44dp touch slots and text size never shrink. */
public final class ComposerStyle {
    public static final int MIN_POSITION = -4, MAX_POSITION = 16;
    public static final int MIN_GAP = 2, MAX_GAP = 8;
    private ComposerStyle() { }
    public static int clamp(int value, int min, int max) { return Math.max(min, Math.min(max, value)); }
    public static int level(int value) { return clamp(value, 0, 2); }
    public static int inset(int level) { return 4 + level(level); }
    public static int diameter(int level) { return ComposerGeometry.TOUCH_SLOT - 2 * inset(level); }
    // Native 18sp text and 44dp touch targets remain intact at every density.
    public static int surface(boolean dark, boolean glass) { return dark ? (glass ? 0xE8303236 : 0xFF303236) : (glass ? 0xF5FAFAFC : 0xFFFAFAFC); }
    public static int icon(boolean dark) { return dark ? 0xFFE1E2E6 : 0xFF62666D; }
    public static int padding(int level) { return 12 - level(level); }
    public static int gap(int level, int custom) { return custom == 0 ? 6 - level(level) : clamp(custom, MIN_GAP, MAX_GAP); }
    // Lowering consumes at most 4dp of the existing 9dp native bottom gap.
    public static int position(int value) { return clamp(value, MIN_POSITION, MAX_POSITION); }
    public static int reserve(int position) { return Math.max(0, position(position)); }
}
