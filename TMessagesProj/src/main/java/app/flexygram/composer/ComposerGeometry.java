package app.flexygram.composer;

/** Presentation constants only: never changes the native IME or measured height. */
public final class ComposerGeometry {
    public static final int TOUCH_SLOT = 44;
    public static final int VISUAL_INSET = 2;
    public static final int PILL_GAP = 6;
    public static final int TEXT_PADDING = 12;
    public static final int TEXT_END_SLOT = 56;
    // Keep the original native 44dp recording/send hit area outside the text pill.
    public static final int TRAILING_ACTION_SLOT = TOUCH_SLOT + PILL_GAP;

    public static float pillLeft(float fieldLeft, float touchSlotPx, float gapPx) {
        return fieldLeft + touchSlotPx + gapPx;
    }

    /** The native field already excludes the send slot; never reserve it twice. */
    public static float pillRight(float fieldRight, float gapPx, float nativeActionTranslation) {
        return fieldRight - gapPx + Math.min(0, nativeActionTranslation);
    }

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
