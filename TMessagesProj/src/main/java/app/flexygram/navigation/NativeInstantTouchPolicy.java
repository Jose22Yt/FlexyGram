/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

/**
 * Decision for a real DOWN during an original Exteraless close. Does not alter
 * curves, speed, gesture events or native animation engines. No user preference.
 */
public final class NativeInstantTouchPolicy {
    private NativeInstantTouchPolicy() {}

    public static boolean canFinishNativeCloseForDown(boolean genuineSingleDown,
            boolean attachedMain, boolean nativeClosing, boolean hasPreviousDialogs,
            boolean hasVisibleDialogRow, boolean outgoingSurfaceCoversTouch,
            boolean previewOrPopup, boolean sheetOrKeyboard,
            boolean nativeGestureOrActionMode) {
        return genuineSingleDown && attachedMain && nativeClosing
                && hasPreviousDialogs && hasVisibleDialogRow
                && !outgoingSurfaceCoversTouch && !previewOrPopup
                && !sheetOrKeyboard && !nativeGestureOrActionMode;
    }
}
