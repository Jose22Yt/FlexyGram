package app.flexygram.kyant;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;

/** The optical overlay must never determine a WRAP_CONTENT navigation bar's height. */
public final class KyantDockContainer extends FrameLayout {
    private final View nativeDock;

    public KyantDockContainer(Context context, View nativeDock) {
        super(context);
        this.nativeDock = nativeDock;
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
            height += dockHeight + params.topMargin + params.bottomMargin;
        }
        // Both the native bar and MATCH_PARENT overlay see the same bounded height on the
        // first measurement pass. A fillMaxSize Compose child cannot expand us to the screen.
        int resolvedHeight = resolveSize(Math.max(height, getSuggestedMinimumHeight()), heightMeasureSpec);
        super.onMeasure(widthMeasureSpec, MeasureSpec.makeMeasureSpec(resolvedHeight, MeasureSpec.EXACTLY));
    }
}
