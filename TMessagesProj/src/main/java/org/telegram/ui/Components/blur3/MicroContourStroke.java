/* SPDX-License-Identifier: GPL-3.0-or-later */
package org.telegram.ui.Components.blur3;
import org.telegram.messenger.AndroidUtilities;
/** Static Android adaptation of a subtle dark glass rim; no blur or frame callback. */
public final class MicroContourStroke {
    public static final int COLOR=0x24000000;
    private MicroContourStroke(){}
    public static float widthPx(){return Math.max(1f,AndroidUtilities.dpf2(0.35f));}
}
