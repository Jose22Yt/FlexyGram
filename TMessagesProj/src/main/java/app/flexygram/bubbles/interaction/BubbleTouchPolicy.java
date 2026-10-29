/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/** Pure conversion admission; original native touch and menu ownership stay unchanged. */
public final class BubbleTouchPolicy {
    private BubbleTouchPolicy() {}
    public static boolean mayConvertToSticker(boolean enabled, boolean messageVisible,
            boolean protectedContent, boolean ephemeral, boolean spoilerHidden,
            boolean supportedStaticMessage, boolean canSendHere) {
        return enabled && messageVisible && !protectedContent && !ephemeral
                && !spoilerHidden && supportedStaticMessage && canSendHere;
    }
}
