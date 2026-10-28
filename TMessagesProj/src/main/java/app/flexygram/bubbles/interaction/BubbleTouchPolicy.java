/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/** Pure admission policy; host keeps original ACTION_DOWN/MOVE/UP ownership. */
public final class BubbleTouchPolicy {
    private BubbleTouchPolicy() {}
    public static boolean mayAnimate(boolean enabled, boolean messageVisible,
                                     boolean insideBubble, boolean interactiveChild,
                                     boolean selectionMode, boolean previewOrModal) {
        return enabled && messageVisible && insideBubble && !interactiveChild
                && !selectionMode && !previewOrModal;
    }
    public static boolean mayConvertToSticker(boolean enabled, boolean messageVisible,
            boolean protectedContent, boolean ephemeral, boolean spoilerHidden,
            boolean supportedStaticMessage, boolean canSendHere) {
        return enabled && messageVisible && !protectedContent && !ephemeral
                && !spoilerHidden && supportedStaticMessage && canSendHere;
    }
}
