package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.widget.FrameLayout;

/** Bounded, non-scrolling host. The complete selected message is fitted above the actions.
 */
public final class MessageMenuViewport extends FrameLayout {
    private int viewportHeight;

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
