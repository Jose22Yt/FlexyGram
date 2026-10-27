/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.view.MotionEvent;
import android.view.View;

/**
 * Opt-in, non-consuming tactile feedback for existing clickable views.
 * The host must forward its MotionEvents from dispatchTouchEvent (not replace
 * Telegram's gesture or click listeners). A single owner controls scale.
 */
public final class FlexyTouchFeedback {
    private final View view;
    private final FlexyFrameMotion scale;
    private float originalX;
    private float originalY;
    private boolean active;

    public FlexyTouchFeedback(View view) {
        this.view = view;
        originalX = view.getScaleX();
        originalY = view.getScaleY();
        scale = new FlexyFrameMotion(view, 1f, factor -> {
            view.setScaleX(originalX * factor);
            view.setScaleY(originalY * factor);
        });
    }

    /** Does not consume or alter the event; preserves native click/drag behavior. */
    public void onTouch(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                if (!active) {
                    originalX = view.getScaleX();
                    originalY = view.getScaleY();
                }
                active = true;
                FlexyMotionProfile profile = FlexyMotionSettings.effectiveProfile(view.getContext());
                scale.animateTo(profile.pressedScale);
                break;
            case MotionEvent.ACTION_MOVE:
                if (active) {
                    float x = event.getX(), y = event.getY();
                    if (x < 0 || y < 0 || x > view.getWidth() || y > view.getHeight()) release();
                }
                break;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                release();
                break;
            default:
                break;
        }
    }

    public void release() {
        if (!active) return;
        active = false;
        scale.animateTo(1f);
    }

    /** Call from the host's onDetachedFromWindow, especially for recycled rows. */
    public void reset() {
        active = false;
        scale.snapTo(1f);
    }

    public void dispose() {
        reset();
        scale.dispose();
    }
}
