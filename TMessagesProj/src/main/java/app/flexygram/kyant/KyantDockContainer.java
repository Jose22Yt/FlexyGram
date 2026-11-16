package app.flexygram.kyant;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;

/** The optical overlay must never determine a WRAP_CONTENT navigation bar's height. */
public final class KyantDockContainer extends FrameLayout {
    public static final int OPTICAL_GUTTER_DP = 24;
    private final View nativeDock;
    public int opticalGutterPx() { return Math.round(OPTICAL_GUTTER_DP * getResources().getDisplayMetrics().density); }
    private boolean isOpticalOverlay(View child) {
        return child != nativeDock && child.getLayoutParams().height == LayoutParams.MATCH_PARENT;
    }

    public KyantDockContainer(Context context, View nativeDock) {
        super(context);
        this.nativeDock = nativeDock;
        setClipChildren(false);
        setClipToPadding(false);
        setElevation(0f);
        setBackground(null);
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
        // Reserve transparent drawing space for magnification/refraction and capsule shadows.
        // Only the optical child expands; native bounds, insets and layout height do not change.
        int gutter=opticalGutterPx();
        for(int i=0;i<getChildCount();i++){
            View child=getChildAt(i);
            if(child.getVisibility()!=GONE && isOpticalOverlay(child))
                child.measure(MeasureSpec.makeMeasureSpec(getMeasuredWidth(),MeasureSpec.EXACTLY),
                    MeasureSpec.makeMeasureSpec(resolvedHeight+gutter*2,MeasureSpec.EXACTLY));
        }
    }
    @Override
    protected void onLayout(boolean changed,int left,int top,int right,int bottom) {
        super.onLayout(changed,left,top,right,bottom);
        int gutter=opticalGutterPx();
        for(int i=0;i<getChildCount();i++){
            View child=getChildAt(i);
            if(child.getVisibility()!=GONE && isOpticalOverlay(child))
                child.layout(0,-gutter,getMeasuredWidth(),getMeasuredHeight()+gutter);
        }
    }

}
