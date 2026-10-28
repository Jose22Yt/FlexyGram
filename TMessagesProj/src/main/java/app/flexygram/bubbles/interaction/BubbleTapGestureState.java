/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/** One native pointer stream. Does not intercept, copy or synthesize MotionEvents. */
public final class BubbleTapGestureState {
    private boolean candidate, moved, longPressed;
    private float startX, startY, slopSq;
    public void down(float x, float y, float touchSlop, boolean accepted) {
        clear();
        if (!Float.isFinite(x) || !Float.isFinite(y) || !Float.isFinite(touchSlop)
                || touchSlop < 0) return;
        startX = x;
        startY = y;
        slopSq = touchSlop * touchSlop;
        candidate = accepted;
    }
    /** Returns true when the host should release its press animation. */
    public boolean move(float x, float y) {
        if (!candidate || moved) return false;
        if (!Float.isFinite(x) || !Float.isFinite(y)) {
            moved = true;
            return true;
        }
        float dx = x-startX, dy = y-startY;
        if (dx*dx + dy*dy > slopSq) { moved = true; return true; }
        return false;
    }
    public void longPress() { longPressed = true; }
    /** True only for a qualified, non-interactive bubble click; native click ownership remains unchanged. */
    public boolean up(boolean originalNativeClickAccepted) {
        boolean tap = candidate && !moved && !longPressed && originalNativeClickAccepted;
        clear();
        return tap;
    }
    public void cancel() { clear(); }
    public boolean isPressed() { return candidate && !moved && !longPressed; }
    private void clear() { candidate = moved = longPressed = false; }
}
