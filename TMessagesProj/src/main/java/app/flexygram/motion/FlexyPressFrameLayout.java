/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

import android.content.Context;
import android.graphics.Canvas;
import android.view.MotionEvent;
import android.widget.FrameLayout;

/** Explicit native press host. Draw compression does not own View.scale or consume touch events. */
public class FlexyPressFrameLayout extends FrameLayout implements FlexyPressOwner {
    private FlexyTouchFeedback feedback;
    public FlexyPressFrameLayout(Context context) { super(context); }
    @Override public void setFlexyPressEnabled(boolean enabled) {
        if (enabled && feedback == null) feedback = new FlexyTouchFeedback(this);
        else if (!enabled && feedback != null) { feedback.dispose(); feedback = null; }
    }
    @Override public boolean dispatchTouchEvent(MotionEvent event) {
        if (feedback != null) feedback.onTouch(event);
        return super.dispatchTouchEvent(event);
    }
    @Override public void draw(Canvas canvas) {
        if (feedback == null) { super.draw(canvas); return; }
        final int save = canvas.save();
        if (feedback != null) feedback.transform(canvas);
        super.draw(canvas);
        canvas.restoreToCount(save);
    }
    @Override protected void onDetachedFromWindow() {
        if (feedback != null) feedback.reset();
        super.onDetachedFromWindow();
    }
    @Override protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);
        if (visibility != VISIBLE && feedback != null) feedback.reset();
    }
    @Override public void setEnabled(boolean enabled) {
        super.setEnabled(enabled);
        if (!enabled && feedback != null) feedback.reset();
    }
}
