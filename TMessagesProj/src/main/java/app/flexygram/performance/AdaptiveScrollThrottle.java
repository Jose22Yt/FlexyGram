/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

/**
 * Velocity-aware 90/120 Hz scroll throttle for GPU backdrop blur and heavy animations.
 * Keeps full native refresh-rate fidelity during dragging, slow scrolling, deceleration, and idle;
 * only relaxes redundant GPU blur captures (alternating frames) and pauses heavy decoders during
 * high-speed flings, always flushing a crisp final state before settling.
 */
public final class AdaptiveScrollThrottle {
    public static final int SCROLL_STATE_IDLE = 0;
    public static final int SCROLL_STATE_DRAGGING = 1;
    public static final int SCROLL_STATE_SETTLING = 2;

    public static final float HIGH_REFRESH_THRESHOLD_HZ = 85f;
    public static final int BLUR_FLING_THRESHOLD_DP = 48;
    public static final int HEAVY_PAUSE_THRESHOLD_DP = 56;
    public static final int HEAVY_RESUME_THRESHOLD_DP = 16;

    public static final int HEAVY_OP_NOOP = 0;
    public static final int HEAVY_OP_PAUSE = 1;
    public static final int HEAVY_OP_RESUME = -1;

    private boolean skipNextBlurFrame;
    private boolean blurDeferred;
    private boolean heavyOpsPaused;

    /**
     * Returns true when this scroll frame should invalidate blurred backdrops.
     * On high-refresh displays during fast settling flings, alternates blur capture every 2nd frame
     * (~60 Hz backdrop updates while list motion stays 120 Hz) and marks deferred state so settling
     * always refreshes cleanly.
     */
    public boolean shouldInvalidateBlur(int scrollState, int dy, float refreshRate, float density) {
        final int absDy = Math.abs(dy);
        final float thresholdPx = BLUR_FLING_THRESHOLD_DP * Math.max(1f, density);
        if (refreshRate >= HIGH_REFRESH_THRESHOLD_HZ
                && scrollState == SCROLL_STATE_SETTLING
                && absDy >= thresholdPx) {
            skipNextBlurFrame = !skipNextBlurFrame;
            if (skipNextBlurFrame) {
                blurDeferred = true;
                return false;
            }
            blurDeferred = false;
            return true;
        }
        skipNextBlurFrame = false;
        blurDeferred = false;
        return true;
    }

    /**
     * Call when scroll returns to idle (or stops). Returns true if a blur invalidation was skipped
     * on the final fling frame and must be flushed now.
     */
    public boolean consumeDeferredBlur() {
        skipNextBlurFrame = false;
        if (blurDeferred) {
            blurDeferred = false;
            return true;
        }
        return false;
    }

    /**
     * Decides whether heavy Lottie/GIF/video decoders should pause or resume during fast flings on
     * high-refresh displays.
     */
    public int updateFastFlingHeavyOps(int scrollState, int dy, float refreshRate, float density) {
        final float safeDensity = Math.max(1f, density);
        if (scrollState != SCROLL_STATE_SETTLING) {
            return releaseHeavyOps() ? HEAVY_OP_RESUME : HEAVY_OP_NOOP;
        }
        final int absDy = Math.abs(dy);
        if (!heavyOpsPaused) {
            if (refreshRate >= HIGH_REFRESH_THRESHOLD_HZ && absDy >= HEAVY_PAUSE_THRESHOLD_DP * safeDensity) {
                heavyOpsPaused = true;
                return HEAVY_OP_PAUSE;
            }
            return HEAVY_OP_NOOP;
        }
        if (absDy <= HEAVY_RESUME_THRESHOLD_DP * safeDensity) {
            heavyOpsPaused = false;
            return HEAVY_OP_RESUME;
        }
        return HEAVY_OP_NOOP;
    }

    /** Unconditionally clears paused state; returns true if caller must post resume notification. */
    public boolean releaseHeavyOps() {
        if (heavyOpsPaused) {
            heavyOpsPaused = false;
            return true;
        }
        return false;
    }

    public boolean isHeavyOpsPaused() {
        return heavyOpsPaused;
    }
}
