package app.flexygram.settings;

import android.content.Context;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.AnimatedTextView;

/** Native selector row: full-width title, value below only when they would collide. */
public final class MatteTextSettingsCell extends TextSettingsCell {
    private boolean stacked;
    private int inset;
    private int gap;
    private int valueGravity = -1;

    public MatteTextSettingsCell(Context context, Theme.ResourcesProvider provider) {
        super(context, provider);
        getTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        getValueTextView().setTextSize(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 14,
                getResources().getDisplayMetrics()));
    }

    private void wrapTitle() {
        getTextView().setSingleLine(false);
        getTextView().setMaxLines(Integer.MAX_VALUE);
        getTextView().setEllipsize(null);
    }

    @Override public void setText(CharSequence text, boolean divider) {
        super.setText(text, divider);
        wrapTitle();
    }

    @Override public void setTextAndValue(CharSequence text, CharSequence value, boolean animated, boolean divider, boolean neko) {
        super.setTextAndValue(text, value, animated, divider, neko);
        wrapTitle();
    }

    @Override
    protected void onMeasure(int widthSpec, int heightSpec) {
        TextView title = getTextView();
        AnimatedTextView value = getValueTextView();
        inset = AndroidUtilities.dp(21);
        gap = AndroidUtilities.dp(8);
        int width = MeasureSpec.getSize(widthSpec);
        int available = Math.max(0, width - inset * 2);
        CharSequence text = value.getText();
        boolean hasValue = value.getVisibility() == View.VISIBLE && !TextUtils.isEmpty(text);
        int valueWidth = hasValue ? (int) Math.ceil(title.getPaint().measureText(text, 0, text.length())) : 0;
        CharSequence label = title.getText();
        float titleWidth = title.getPaint().measureText(label, 0, label.length());
        stacked = hasValue && MatteSettingsLayout.stackValue(titleWidth, valueWidth, available, gap);
        int titleWidthPx = stacked || !hasValue ? available : Math.max(0, available - valueWidth - gap);
        title.measure(MeasureSpec.makeMeasureSpec(titleWidthPx, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
        int valueHeight = hasValue ? (int) Math.ceil(title.getLineHeight()) : 0;
        value.measure(MeasureSpec.makeMeasureSpec(stacked ? available : Math.min(available, valueWidth), MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(valueHeight, MeasureSpec.EXACTLY));
        int height = MatteSettingsLayout.rowHeight(AndroidUtilities.dp(50), title.getMeasuredHeight(),
                stacked ? valueHeight : 0, AndroidUtilities.dp(12), AndroidUtilities.dp(4));
        setMeasuredDimension(width, height + (needDivider ? 1 : 0));
    }

    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        // This subtype is used only for text/value settings rows, never icon/loading rows.
        TextView title = getTextView();
        AnimatedTextView value = getValueTextView();
        boolean rtl = LocaleController.isRTL;
        int contentHeight = getMeasuredHeight() - (needDivider ? 1 : 0);
        int titleTop = stacked ? AndroidUtilities.dp(12) : (contentHeight - title.getMeasuredHeight()) / 2;
        int titleLeft = rtl ? getMeasuredWidth() - inset - title.getMeasuredWidth() : inset;
        title.layout(titleLeft, titleTop, titleLeft + title.getMeasuredWidth(), titleTop + title.getMeasuredHeight());
        int gravity = (stacked ? (rtl ? Gravity.RIGHT : Gravity.LEFT) : (rtl ? Gravity.LEFT : Gravity.RIGHT)) | Gravity.CENTER_VERTICAL;
        if (valueGravity != gravity) {
            value.setGravity(gravity);
            valueGravity = gravity;
        }
        int valueTop = stacked ? titleTop + title.getMeasuredHeight() + AndroidUtilities.dp(4)
                : (contentHeight - value.getMeasuredHeight()) / 2;
        int valueLeft = stacked ? inset : rtl ? inset : getMeasuredWidth() - inset - value.getMeasuredWidth();
        value.layout(valueLeft, valueTop, valueLeft + value.getMeasuredWidth(), valueTop + value.getMeasuredHeight());
    }
}
