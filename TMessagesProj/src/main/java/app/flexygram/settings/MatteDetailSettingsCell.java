package app.flexygram.settings;

import android.content.Context;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.Cells.TextDetailSettingsCell;

/** Keeps native icons/clicks and measures the subtitle after the complete title. */
public final class MatteDetailSettingsCell extends TextDetailSettingsCell {
    private final app.flexygram.motion.FlexyTouchFeedback motion = new app.flexygram.motion.FlexyTouchFeedback(this);
    public void resetMotion() { if (motion != null) motion.reset(); }
    @Override public boolean dispatchTouchEvent(android.view.MotionEvent event) {
        motion.onTouch(event);
        return super.dispatchTouchEvent(event);
    }
    @Override protected void dispatchDraw(android.graphics.Canvas canvas) {
        int save = canvas.save();
        motion.transform(canvas);
        super.dispatchDraw(canvas);
        canvas.restoreToCount(save);
    }
    @Override protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);
        if (visibility != View.VISIBLE) resetMotion();
    }

    public MatteDetailSettingsCell(Context context) {
        super(context);
        getTextView().setSingleLine(false);
        getTextView().setMaxLines(Integer.MAX_VALUE);
        getTextView().setEllipsize(null);
        getTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        getValueTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        for (int i = 0; i < getChildCount(); i++) {
            View child = getChildAt(i);
            FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) child.getLayoutParams();
            if (child instanceof ImageView) {
                params.gravity = (params.gravity & Gravity.HORIZONTAL_GRAVITY_MASK) | Gravity.CENTER_VERTICAL;
                params.topMargin = 0;
            } else if (child instanceof TextView) {
                params.width = LayoutParams.MATCH_PARENT;
            }
        }
    }

    @Override
    protected void onMeasure(int widthSpec, int heightSpec) {
        TextView title = getTextView();
        FrameLayout.LayoutParams titleParams = (FrameLayout.LayoutParams) title.getLayoutParams();
        int width = MeasureSpec.getSize(widthSpec);
        title.measure(MeasureSpec.makeMeasureSpec(Math.max(0, width - titleParams.leftMargin - titleParams.rightMargin), MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
        ((FrameLayout.LayoutParams) getValueTextView().getLayoutParams()).topMargin =
                titleParams.topMargin + title.getMeasuredHeight() + AndroidUtilities.dp(4);
        super.onMeasure(widthSpec, heightSpec);
        setMeasuredDimension(width, Math.max(AndroidUtilities.dp(64), getMeasuredHeight()));
    }
}
