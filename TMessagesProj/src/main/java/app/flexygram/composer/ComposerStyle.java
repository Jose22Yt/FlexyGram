package app.flexygram.composer;

/** Bounded presentation policy. Native 44dp touch slots and text size never shrink. */
public final class ComposerStyle {
    public static final int MIN_POSITION = -4, MAX_POSITION = 16;
    public static final int MIN_GAP = 2, MAX_GAP = 8;
    private ComposerStyle() { }
    public static int clamp(int value, int min, int max) { return Math.max(min, Math.min(max, value)); }
    public static int level(int value) { return clamp(value, 0, 2); }
    public static int inset(int level) { return 2 * level(level); }
    public static int diameter(int level) { return ComposerGeometry.TOUCH_SLOT - 2 * inset(level); }
    // Native 18sp text and 44dp touch targets remain intact at every density.
    public static int surface(boolean dark, boolean glass) { return dark ? (glass ? 0xE8303236 : 0xFF303236) : (glass ? 0xF5FAFAFC : 0xFFFAFAFC); }
    public static int icon(boolean dark) { return dark ? 0xFFF0F1F4 : 0xFF202329; }
    public static int innerIcon(boolean dark) { return dark ? 0xFFA6A8AE : 0xFF687078; }
    public static int padding(int level) { return 14 - level(level); }
    public static int gap(int level, int custom) { return custom == 0 ? 6 - level(level) : clamp(custom, MIN_GAP, MAX_GAP); }
    // Lowering consumes at most 4dp of the existing 9dp native bottom gap.
    public static int position(int value) { return clamp(value, MIN_POSITION, MAX_POSITION); }
    public static int offset(int position) { return 10 + position(position); }
    public static int reserve(int position) { return offset(position); }
    /** Screenshot proportions; keep enough native field width on narrow windows. */
    public static int sideMargin(int widthPx, float density, int nativeMargin) {
        int reference = Math.min(Math.round(widthPx * 0.065f), Math.round(32 * density));
        int available = (widthPx - Math.round((ComposerGeometry.TOUCH_SLOT + 280) * density)) / 2;
        return Math.max(nativeMargin, Math.min(reference, available));
    }
}
