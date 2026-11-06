package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.widget.ScrollView;

/** Scroll the complete selection (reactions, original-sized message, actions) together. */
public final class MessageMenuScrollView extends ScrollView {
    public interface Listener { void onScroll(int offset); }
    private int viewportHeight;
    private final Listener listener;

    public MessageMenuScrollView(Context context, Listener listener) {
        super(context);
        this.listener = listener;
        setFillViewport(false);
        setVerticalScrollBarEnabled(true);
        setOverScrollMode(OVER_SCROLL_NEVER);
    }

    public void setViewportHeight(int height) {
        height = Math.max(1, height);
        if (viewportHeight == height) return;
        viewportHeight = height;
        requestLayout();
    }

    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        if (viewportHeight > 0) {
            int limit = viewportHeight;
            if (MeasureSpec.getMode(heightSpec) != MeasureSpec.UNSPECIFIED)
                limit = Math.min(limit, MeasureSpec.getSize(heightSpec));
            heightSpec = MeasureSpec.makeMeasureSpec(limit, MeasureSpec.AT_MOST);
        }
        super.onMeasure(widthSpec, heightSpec);
    }

    @Override protected void onScrollChanged(int x, int y, int oldX, int oldY) {
        super.onScrollChanged(x, y, oldX, oldY);
        if (listener != null) listener.onScroll(y);
    }
}
