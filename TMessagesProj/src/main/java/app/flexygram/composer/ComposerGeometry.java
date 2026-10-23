package app.flexygram.composer;

/** Presentation constants only: never changes the native IME or measured height. */
public final class ComposerGeometry {
    public static final int TOUCH_SLOT = 44;
    public static final int VISUAL_INSET = 2;
    public static final int PILL_GAP = 6;
    public static final int TEXT_END_SLOT = 50;

    private ComposerGeometry() { }

    public static boolean supportsCompact(float widthDp, boolean nativeSpecialControls) {
        return widthDp >= 280 && !nativeSpecialControls;
    }

    public static int textEnd(int nativeEnd, int slotPx, boolean compact) {
        return compact ? Math.max(nativeEnd, slotPx) : nativeEnd;
    }

    public static float visualHeight(float nativeHeight, float inset) {
        return Math.max(0, nativeHeight - inset * 2);
    }
}
