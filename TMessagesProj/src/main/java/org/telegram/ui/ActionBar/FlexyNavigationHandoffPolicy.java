/*
 * FlexyGram Instant Navigation: conservative exposed-surface handoff policy.
 * Pure Java by design, so Android view ownership is tested separately.
 */
package org.telegram.ui.ActionBar;

public final class FlexyNavigationHandoffPolicy {

    private FlexyNavigationHandoffPolicy() {
    }

    /**
     * True only when an in-flight outgoing screen has exposed a real hit region
     * of its already-attached destination. Never retarget a touch from beneath
     * an opaque outgoing view, or from a preview/modal/gesture transition.
     *
     * The caller must additionally validate the fragment types, ACTION_DOWN,
     * overlay ownership, and the transition-completion callback.
     */
    public static boolean canHandoffClosingDown(
            boolean hasClosingTransition,
            boolean blockedByModalOrGesture,
            boolean outgoingVisible,
            boolean destinationAttached,
            float touchX,
            float touchY,
            float outgoingTranslationX,
            float width,
            float height,
            float safetyInset) {
        if (!hasClosingTransition || blockedByModalOrGesture || !outgoingVisible || !destinationAttached) {
            return false;
        }
        if (!finite(touchX) || !finite(touchY) || !finite(outgoingTranslationX)
                || !finite(width) || !finite(height) || !finite(safetyInset)) {
            return false;
        }
        if (width <= 0f || height <= 0f || safetyInset < 0f
                || outgoingTranslationX <= safetyInset * 2f
                || outgoingTranslationX > width) {
            return false;
        }
        // A conservative interior region, outside the animated outgoing view.
        // No synthetic MotionEvent is generated: Android still owns DOWN/UP.
        return touchX >= safetyInset
                && touchX < outgoingTranslationX - safetyInset
                && touchY >= safetyInset
                && touchY < height - safetyInset;
    }

    private static boolean finite(float value) {
        return !Float.isNaN(value) && !Float.isInfinite(value);
    }
}
