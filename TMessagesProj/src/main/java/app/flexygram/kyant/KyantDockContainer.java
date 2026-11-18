package app.flexygram.kyant;

import android.content.Context;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;

/** The optical overlay must never determine a WRAP_CONTENT navigation bar's height. */
public final class KyantDockContainer extends FrameLayout {
    private final View nativeDock;
    private int opticalTopInset;

    public KyantDockContainer(Context context, View nativeDock) {
        super(context);
        this.nativeDock = nativeDock;
    }

    public void setOpticalTopInset(int pixels) {
        if (opticalTopInset == pixels) return;
        opticalTopInset = pixels;
        requestLayout();
    }

    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        // The taller host is for drawing. A new touch above the original bar
        // should still reach the underlying list. Active drag sequences continue.
        if (event.getActionMasked() == MotionEvent.ACTION_DOWN
                && (nativeDock.getVisibility() != VISIBLE || event.getY() < opticalTopInset)) {
            return false;
        }
        return super.dispatchTouchEvent(event);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int height = getPaddingTop() + getPaddingBottom();
        if (nativeDock.getVisibility() != GONE) {
            LayoutParams params = (LayoutParams) nativeDock.getLayoutParams();
            int dockHeight = params.height;
            if (dockHeight < 0) {
                measureChildWithMargins(nativeDock, widthMeasureSpec, 0, heightMeasureSpec, 0);
                dockHeight = nativeDock.getMeasuredHeight();
            }
            height += opticalTopInset + dockHeight + params.topMargin + params.bottomMargin;
        }
        // Both the native bar and MATCH_PARENT overlay see the same bounded height on the
        // first measurement pass. A fillMaxSize Compose child cannot expand us to the screen.
        int resolvedHeight = resolveSize(Math.max(height, getSuggestedMinimumHeight()), heightMeasureSpec);
        super.onMeasure(widthMeasureSpec, MeasureSpec.makeMeasureSpec(resolvedHeight, MeasureSpec.EXACTLY));
    }
}
