package app.flexygram.settings;

/** Measurement policy shared by real native cells and host regression tests. */
public final class MatteSettingsLayout {
    private MatteSettingsLayout() {}

    public static boolean stackValue(float titleWidth, float valueWidth, int available, int gap) {
        return valueWidth > 0 && titleWidth + valueWidth + gap > Math.max(0, available);
    }

    public static int rowHeight(int minimum, int titleHeight, int valueHeight, int padding, int gap) {
        return Math.max(minimum, titleHeight + valueHeight + padding * 2 + (valueHeight > 0 ? gap : 0));
    }
}
