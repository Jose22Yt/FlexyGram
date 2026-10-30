/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Pure, allocation-free width policy for existing DialogCell preview rows. */
public final class SignatureSmartPillLayout {
    private SignatureSmartPillLayout() {}

    /**
     * Width available to the adjacent filename or snippet. Never request
     * geometry outside the row and leave a guard margin for native ellipsis.
     */
    public static int remaining(float lineWidth, float senderWidth,
                                int thumbnailWidth, int badgeWidth, int guardPixels) {
        if (!Float.isFinite(lineWidth) || lineWidth <= 0 || !Float.isFinite(senderWidth)) return 0;
        return Math.max(0, (int) Math.floor(lineWidth - Math.max(0f, senderWidth)
                - Math.max(0, thumbnailWidth) - Math.max(0, badgeWidth)
                - Math.max(0, guardPixels)));
    }
}
