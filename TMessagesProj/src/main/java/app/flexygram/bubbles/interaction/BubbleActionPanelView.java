/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Vertical presentation only. ChatActivity revalidates native permissions on every action. */
public final class BubbleActionPanelView extends LinearLayout {
    public enum Action { REPLY, COPY, FORWARD, EDIT, PIN, DELETE, SELECT, MORE }
    public interface Listener { void onAction(Action action); }
    private Listener listener;
    private java.util.EnumSet<Action> allowed = java.util.EnumSet.noneOf(Action.class);
    private static int dp(Context c, float v) {
        return (int) (c.getResources().getDisplayMetrics().density * v + .5f);
    }
    public BubbleActionPanelView(Context context, Theme.ResourcesProvider provider) {
        super(context);
        setOrientation(VERTICAL);
        setPadding(0, dp(context, 4), 0, dp(context, 4));
        // The native popup owns the translucent surface and coordinated entry/exit timeline.
    }
    public void setListener(Listener value) { listener = value; }
    public void setAllowedActions(java.util.EnumSet<Action> actions) {
        allowed = actions.clone();
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
        Context c = getContext();
        String label = LocaleController.getString(stringId);
        int color = 0xfff5f7fa;
        LinearLayout row = new LinearLayout(c);
        row.setOrientation(HORIZONTAL);
        row.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(c, 14), 0, dp(c, 14), 0);
        ImageView icon = new ImageView(c);
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setImageResource(iconId);
        icon.setColorFilter(color);
        row.addView(icon, new LayoutParams(dp(c, 21), dp(c, 21)));
        TextView text = new TextView(c);
        text.setText(label);
        text.setTextSize(15);
        text.setTextColor(color);
        text.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        text.setMaxLines(2);
        LayoutParams lp = new LayoutParams(0, -2, 1f);
        lp.leftMargin = dp(c, 14);
        row.addView(text, lp);
        // Compact visual rows retain accessible 48dp touch targets; font scaling can grow them.
        row.setMinimumHeight(dp(c, 48));
        row.setPadding(dp(c, 14), dp(c, 6), dp(c, 14), dp(c, 6));
        row.setBackground(new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(0x20ffffff), null, null));
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
