/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.drawable.RippleDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/**
 * Compact iOS-style vertical presentation. Native ChatActivity owns permission
 * checks and action dispatch; this view never bypasses Telegram restrictions.
 */
public final class BubbleActionPanelView extends LinearLayout {
    public enum Action { REPLY, COPY, FORWARD, EDIT, PIN, DELETE, SELECT, MORE }
    public interface Listener { void onAction(Action action); }
    private Listener listener;
    private java.util.EnumSet<Action> allowed = java.util.EnumSet.noneOf(Action.class);
    private final int textColor;
    private static int dp(Context c, float v) {
        return (int) (c.getResources().getDisplayMetrics().density * v + .5f);
    }

    public BubbleActionPanelView(Context context, Theme.ResourcesProvider provider) {
        super(context);
        setOrientation(VERTICAL);
        setPadding(0, dp(context, 3), 0, dp(context, 3));
        // The native popup owns the themed surface; use its foreground palette.
        textColor = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, provider);
    }

    public void setListener(Listener value) { listener = value; }

    public void setAllowedActions(java.util.EnumSet<Action> actions) {
        allowed = actions == null ? java.util.EnumSet.noneOf(Action.class) : actions.clone();
        removeAllViews();
        line(R.string.Reply, R.drawable.msg_reply_small, Action.REPLY);
        line(R.string.Copy, R.drawable.msg_copy, Action.COPY);
        line(R.string.Forward, R.drawable.msg_forward, Action.FORWARD);
        line(R.string.Edit, R.drawable.msg_edit, Action.EDIT);
        line(R.string.PinToTop, R.drawable.msg_pin, Action.PIN);
        line(R.string.Delete, R.drawable.msg_delete, Action.DELETE);
        line(R.string.FlexyContextMore, R.drawable.msg_other_new_outline, Action.MORE);
    }

    private void line(int stringId, int iconId, Action action) {
        if (action != Action.MORE && !allowed.contains(action)) return;
        final Context c = getContext();
        final String label = LocaleController.getString(stringId);
        final int color = action == Action.DELETE ? 0xffdf5363 : textColor;
        if (getChildCount() > 0) {
            View divider = new View(c);
            divider.setBackgroundColor((textColor & 0x00ffffff) | 0x18000000);
            LayoutParams dividerParams = new LayoutParams(-1, dp(c, 1));
            dividerParams.leftMargin = dp(c, 14);
            dividerParams.rightMargin = dp(c, 14);
            addView(divider, dividerParams);
        }

        LinearLayout row = new LinearLayout(c);
        row.setOrientation(HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(c, 14), dp(c, 5), dp(c, 14), dp(c, 5));
        row.setMinimumHeight(dp(c, 48));

        ImageView icon = new ImageView(c);
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setImageResource(iconId);
        icon.setColorFilter(color);
        row.addView(icon, new LayoutParams(dp(c, 20), dp(c, 20)));

        TextView title = new TextView(c);
        title.setText(label);
        title.setTextSize(15);
        title.setTextColor(color);
        title.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        title.setSingleLine(true);
        title.setEllipsize(TextUtils.TruncateAt.END);
        LayoutParams titleParams = new LayoutParams(0, -2, 1f);
        titleParams.leftMargin = dp(c, 12);
        row.addView(title, titleParams);

        int ripple = (textColor & 0x00ffffff) | 0x18000000;
        row.setBackground(new RippleDrawable(ColorStateList.valueOf(ripple), null, null));
        row.setContentDescription(label);
        row.setFocusable(true);
        row.setOnClickListener(v -> {
            if (listener != null && (action == Action.MORE || allowed.contains(action)))
                listener.onAction(action);
        });
        addView(row, new LayoutParams(-1, -2));
    }

    @Override protected void onDetachedFromWindow() {
        listener = null;
        super.onDetachedFromWindow();
    }
}
