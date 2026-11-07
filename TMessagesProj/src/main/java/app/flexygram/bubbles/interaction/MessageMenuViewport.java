package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.view.MotionEvent;
import android.widget.FrameLayout;

/** Bounded, non-scrolling host. The complete selected message is fitted above the actions.
 */
public final class MessageMenuViewport extends FrameLayout {
    private int viewportHeight;
    private Runnable dismissRequest;
    private boolean dismissGesture;

    public MessageMenuViewport(Context context) {
        super(context);
        setDescendantFocusability(FOCUS_BEFORE_DESCENDANTS);
        setFocusableInTouchMode(true);
    }

    public void setViewportHeight(int height) {
        height = Math.max(1, height);
        if (viewportHeight == height) return;
        viewportHeight = height;
        requestLayout();
    }

    public void setDismissRequest(Runnable request) { dismissRequest = request; }

    @Override public boolean dispatchTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) dismissGesture = false;
        if (dismissGesture) {
            if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) dismissGesture = false;
            return true;
        }
        if (action == MotionEvent.ACTION_OUTSIDE && dismissRequest != null) {
            dismissRequest.run();
            return true;
        }
        boolean handled = super.dispatchTouchEvent(event);
        if (action == MotionEvent.ACTION_DOWN && !handled && dismissRequest != null) {
            dismissGesture = true;
            dismissRequest.run();
            return true;
        }
        return handled;
    }

    @Override public void scrollTo(int x, int y) { super.scrollTo(0, 0); }

    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        if (viewportHeight > 0) {
            int limit = viewportHeight;
            if (MeasureSpec.getMode(heightSpec) != MeasureSpec.UNSPECIFIED)
                limit = Math.min(limit, MeasureSpec.getSize(heightSpec));
            heightSpec = MeasureSpec.makeMeasureSpec(limit, MeasureSpec.AT_MOST);
        }
        super.onMeasure(widthSpec, heightSpec);
    }
}
