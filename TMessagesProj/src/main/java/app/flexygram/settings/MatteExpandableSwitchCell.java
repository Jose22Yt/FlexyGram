package app.flexygram.settings;

import android.content.Context;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.Cells.TextCheckCell2;

/** Original group toggle/arrow callbacks, with distinct title/counter/switch bounds. */
public final class MatteExpandableSwitchCell extends TextCheckCell2 {
    public MatteExpandableSwitchCell(Context context) {
        super(context);
        ((TextView) getChildAt(0)).setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
    }

    @Override public void setTextAndCheck(String text, boolean checked, boolean divider, boolean animated) {
        super.setTextAndCheck(text, checked, divider, animated);
        TextView title = (TextView) getChildAt(0);
        title.setSingleLine(false);
        title.setMaxLines(Integer.MAX_VALUE);
        title.setEllipsize(null);
        FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) title.getLayoutParams();
        params.width = LayoutParams.MATCH_PARENT;
        params.height = LayoutParams.WRAP_CONTENT;
        params.gravity = (LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT) | Gravity.CENTER_VERTICAL;
        // 76dp existing toggle hit area, 48dp counter/chevron, 21dp title inset.
        params.leftMargin = AndroidUtilities.dp(LocaleController.isRTL ? 124 : 21);
        params.rightMargin = AndroidUtilities.dp(LocaleController.isRTL ? 21 : 124);
    }

    @Override public void onInitializeAccessibilityNodeInfo(android.view.accessibility.AccessibilityNodeInfo info) {
        super.onInitializeAccessibilityNodeInfo(info);
        info.setText(((TextView) getChildAt(0)).getText());
    }

    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        super.onMeasure(widthSpec, heightSpec);
        TextView title = (TextView) getChildAt(0);
        FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) title.getLayoutParams();
        title.measure(MeasureSpec.makeMeasureSpec(Math.max(0, MeasureSpec.getSize(widthSpec) - params.leftMargin - params.rightMargin), MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
        int height = Math.max(getMeasuredHeight(), title.getMeasuredHeight() + AndroidUtilities.dp(24));
        setMeasuredDimension(MeasureSpec.getSize(widthSpec), height);
        int exactHeight = MeasureSpec.makeMeasureSpec(height, MeasureSpec.EXACTLY);
        for (int i = 1; i < getChildCount(); i++) {
            View child = getChildAt(i);
            if (child.getVisibility() != GONE) measureChildWithMargins(child, widthSpec, 0, exactHeight, 0);
        }
    }
}
