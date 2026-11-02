/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.graphics.PorterDuff;
import android.graphics.PorterDuffColorFilter;

/** One cache per native tab: alternating selected/unselected tabs cannot thrash it. */
public final class SignatureHomeTint {
    private int color;
    private PorterDuffColorFilter filter;

    public PorterDuffColorFilter get(int requested) {
        if (filter == null || color != requested) {
            color = requested;
            filter = new PorterDuffColorFilter(requested, PorterDuff.Mode.SRC_IN);
        }
        return filter;
    }
}
