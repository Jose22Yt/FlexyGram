package app.flexygram.settings;

import android.content.Context;
import android.util.TypedValue;
import android.view.View;
import android.widget.TextView;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCheckCell;

/** Native switch/ripple/state handling; descriptions grow with Android font scaling. */
public final class MatteTextCheckCell extends TextCheckCell {
    public MatteTextCheckCell(Context context, Theme.ResourcesProvider provider) {
        super(context, provider);
        setWrapTitle(true);
        for (int i = 0; i < getChildCount(); i++) {
            View child = getChildAt(i);
            if (child instanceof TextView) {
                ((TextView) child).setTextSize(TypedValue.COMPLEX_UNIT_SP, i == 0 ? 16 : 13);
            }
        }
    }

    @Override
    public void setTextAndValueAndCheck(String text, String value, boolean checked,
                                       boolean multiline, boolean divider, boolean neko) {
        // The original 64dp single-line-detail branch clips scaled descriptions.
        // Delegate to the native variable-height branch, retaining its switch callbacks.
        super.setTextAndValueAndCheck(text, value, checked, true, divider, false);
    }
}
