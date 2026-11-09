/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.os.Build;
import android.view.View;

/** A transient Android ARR vote, never a frame loop or a fixed display-mode override. */
public final class ScrollFrameRateHint {
    private final View owner;
    private boolean active;
    private float previous;
    public ScrollFrameRateHint(View owner) { this.owner = owner; }
    public void setScrolling(boolean scrolling) {
        if (scrolling == active) return;
        active = scrolling;

        if (Build.VERSION.SDK_INT >= 35) {
            try {
                if (scrolling) {
                    previous = owner.getRequestedFrameRate();
                    owner.setRequestedFrameRate(View.REQUESTED_FRAME_RATE_CATEGORY_HIGH);
                } else if (owner.getRequestedFrameRate() == View.REQUESTED_FRAME_RATE_CATEGORY_HIGH) {
                    // Preserve an intervening owner's explicit request instead of overwriting it.
                    owner.setRequestedFrameRate(previous);
                }
            } catch (Throwable ignore) {
            }
        }

        if (Build.VERSION.SDK_INT >= 30) {
            try {
                owner.setFrameContentVelocity(scrolling ? 1000.0f : 0.0f);
            } catch (Throwable ignore) {
            }
        }
    }
}
