/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.view.animation.DecelerateInterpolator;
import org.telegram.ui.ActionBar.Theme;

/**
 * Signature Matte presentation of host-approved actions only. Native ChatActivity owns all action
 * permissions and onClick outcomes. Never synthesizes clicks or sends messages.
 * Host must keep the selected MessageObject/peer and invalidate on detach.
 */
public final class BubbleActionPanelView extends LinearLayout {
    public enum Action { REPLY, COPY, FORWARD, EDIT, PIN, DELETE, SELECT, BUILD_STICKER, SEND_STICKER, SAVE_STICKER, MORE }
    public interface Listener { void onAction(Action action); }

    private static final int TAB_ACTIONS = 0, TAB_STICKER = 1, TAB_SELECT = 2;
    private final LinearLayout content;
    private final LinearLayout tabs;
    private final ImageView stickerPreview;
    private final TextView sendButton;
    private final TextView saveButton, stickerStatus;
    private Runnable onDispose;
    private AnimatorSet bounce;
    public void setOnDispose(Runnable callback) { onDispose=callback; }
    public void setStickerEnabled(boolean enabled) { stickerEnabled=enabled && BubbleInteractionSettings.stickerConversion(getContext()); if (!stickerEnabled && tab==TAB_STICKER) tab=TAB_ACTIONS; refresh(); }
    public void setStickerStatus(String status) { stickerStatus.setText(status); }
    public void setStickerActions(boolean send, boolean save) { sendButton.setEnabled(send); sendButton.setAlpha(send?1f:.5f); saveButton.setEnabled(save); saveButton.setAlpha(save?1f:.5f); }
    private Listener listener;
    private java.util.EnumSet<Action> allowed=java.util.EnumSet.noneOf(Action.class);
    private boolean stickerEnabled;
    public void setAllowedActions(java.util.EnumSet<Action> actions){allowed=actions.clone();refresh();}
    public void setConfiguration(java.util.EnumSet<Action> actions,boolean sticker) {
        allowed=actions.clone();stickerEnabled=sticker && BubbleInteractionSettings.stickerConversion(getContext());
        if(!sticker && tab==TAB_STICKER)tab=TAB_ACTIONS;
        refresh();
    }
    private String label(int id){return org.telegram.messenger.LocaleController.getString(id);}
    private int tab = TAB_ACTIONS;
    private boolean canSendSticker;
    private final int foreground, muted, accent, surface, secondary, danger;
    private static int dp(Context c, float v) {
        return (int)(c.getResources().getDisplayMetrics().density * v + .5f);
    }
    public BubbleActionPanelView(Context context, Theme.ResourcesProvider provider) {
        super(context);
        foreground = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        muted = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2,provider);
        accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider);
        surface = Theme.getColor(Theme.key_windowBackgroundWhite,provider);
        secondary = Theme.getColor(Theme.key_windowBackgroundGray,provider);
        danger = Theme.getColor(Theme.key_text_RedRegular,provider);
        setOrientation(VERTICAL);
        setPadding(dp(context, 9), dp(context, 9), dp(context, 9), dp(context, 10));
        setBackground(round(context, surface, 24));
        tabs = new LinearLayout(context);
        tabs.setOrientation(HORIZONTAL);
        addView(tabs, new LayoutParams(-1, 0));
        tabs.setVisibility(GONE);
        content = new LinearLayout(context);
        content.setOrientation(VERTICAL);
        LayoutParams contentLp = new LayoutParams(-1, -2);
        contentLp.topMargin = 0;
        addView(content, contentLp);
        stickerPreview = new ImageView(context);
        stickerPreview.setScaleType(ImageView.ScaleType.FIT_CENTER);
        sendButton = button(label(org.telegram.messenger.R.string.FlexyContextSendHere), true);
        sendButton.setEnabled(false);
        sendButton.setAlpha(.5f);
        sendButton.setOnClickListener(v -> dispatch(Action.SEND_STICKER));
        saveButton = button(label(org.telegram.messenger.R.string.FlexyContextSave), false);
        saveButton.setOnClickListener(v -> dispatch(Action.SAVE_STICKER));
        stickerStatus = button(label(org.telegram.messenger.R.string.FlexyContextStickerPreparing), false);
        stickerStatus.setBackground(null);
        setStickerActions(false,false);
        refresh();
    }
    private GradientDrawable round(Context c, int color, float radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(c, radius));
        return d;
    }
    public void setListener(Listener listener) { this.listener = listener; }
    public void setStickerPreview(Bitmap preview) {
        stickerPreview.setImageBitmap(preview);
        canSendSticker = preview != null;
        setStickerActions(canSendSticker,canSendSticker);
    }
    public void clearStickerPreview() { setStickerPreview(null); }
    private void dispatch(Action action) {
        if (listener != null && (action==Action.MORE || allowed.contains(action))) listener.onAction(action);
    }
    private TextView button(String label, boolean highlighted) {
        TextView t = new TextView(getContext());
        t.setGravity(Gravity.CENTER);
        t.setText(label);
        t.setTextSize(13);
        t.setTextColor(highlighted ? accent : foreground);
        t.setBackground(round(getContext(), secondary, 14));
        t.setPadding(dp(getContext(), 7), dp(getContext(), 7), dp(getContext(), 7), dp(getContext(), 7));
        return t;
    }
    private void headerTab(String name, int id) {
        TextView t = button(name, id == tab);
        t.setTextColor(id == tab ? accent : muted);
        t.setContentDescription(name);
        LayoutParams p = new LayoutParams(0, -1, 1f);
        p.leftMargin = dp(getContext(), 2);
        p.rightMargin = dp(getContext(), 2);
        tabs.addView(t, p);
        t.setOnClickListener(v -> { tab = id; refresh(); if (id == TAB_STICKER) dispatch(Action.BUILD_STICKER); });
    }

    /** Vector-painted local glyphs: no additional resource pack, allocations or raster assets. */
    private static final class CompactGlyph extends android.graphics.drawable.Drawable {
        private final android.graphics.Paint paint =
                new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final int color;
        private final boolean more;
        CompactGlyph(int color, boolean more) { this.color = color; this.more = more; }
        @Override public void draw(android.graphics.Canvas canvas) {
            android.graphics.Rect bounds = getBounds();
            float size = Math.min(bounds.width(), bounds.height());
            if (size <= 0) return;
            int save = canvas.save();
            canvas.translate(bounds.exactCenterX(), bounds.exactCenterY());
            paint.setColor(color);
            paint.setStyle(android.graphics.Paint.Style.FILL);
            if (more) {
                for (int i = -1; i <= 1; i++)
                    canvas.drawCircle(i * size * .24f, 0f, size * .075f, paint);
            } else {
                float left = -size * .38f, top = -size * .38f, right = size * .38f;
                paint.setStyle(android.graphics.Paint.Style.STROKE);
                paint.setStrokeWidth(size * .075f);
                paint.setStrokeJoin(android.graphics.Paint.Join.ROUND);
                canvas.drawRoundRect(left, top, right, right, size * .14f, size * .14f, paint);
                canvas.drawLine(size * .09f, right, right, size * .09f, paint);
                canvas.drawCircle(-size * .15f, -size * .10f, size * .018f, paint);
                canvas.drawCircle(size * .10f, -size * .10f, size * .018f, paint);
                canvas.drawArc(-size * .16f, -size * .12f, size * .13f, size * .17f,
                        12f, 140f, false, paint);
            }
            canvas.restoreToCount(save);
        }
        @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(android.graphics.ColorFilter filter) {
            paint.setColorFilter(filter); invalidateSelf();
        }
        @Override public int getOpacity() { return android.graphics.PixelFormat.TRANSLUCENT; }
    }
    private void addTile(LinearLayout row, String title, int icon, Action action) {
        if (action != Action.MORE && !allowed.contains(action)) return;
        LinearLayout tile = new LinearLayout(getContext());
        tile.setGravity(Gravity.CENTER);
        tile.setOrientation(VERTICAL);
        tile.setBackground(round(getContext(), secondary, 13));
        ImageView glyph = new ImageView(getContext());
        glyph.setScaleType(ImageView.ScaleType.FIT_CENTER);
        if (action == Action.MORE) glyph.setImageDrawable(new CompactGlyph(foreground, true));
        else glyph.setImageResource(icon);
        glyph.setColorFilter(action == Action.DELETE ? danger : foreground);
        tile.addView(glyph, new LayoutParams(-1, dp(getContext(), 26)));
        TextView label = new TextView(getContext());
        label.setText(title);
        label.setTextSize(11);
        label.setTextColor(action == Action.DELETE ? danger : foreground);
        label.setGravity(Gravity.CENTER);
        tile.addView(label, new LayoutParams(-1, dp(getContext(), 19)));
        LayoutParams p = new LayoutParams(0, dp(getContext(), 64), 1f);
        p.leftMargin = dp(getContext(), 2);
        p.rightMargin = dp(getContext(), 2);
        row.addView(tile, p);
        tile.setContentDescription(title);tile.setFocusable(true);
        tile.setOnClickListener(v -> dispatch(action));
    }

    /** Short context surface; native host remains the sole permission/action authority. */
    private void actionLine(String name, int icon, Action action, boolean highlighted) {
        if (action == Action.BUILD_STICKER ? !stickerEnabled || !allowed.contains(action)
                : !allowed.contains(action)) return;
        LinearLayout line = new LinearLayout(getContext());
        line.setOrientation(HORIZONTAL);
        line.setGravity(Gravity.CENTER_VERTICAL);
        line.setPadding(dp(getContext(), 12), 0, dp(getContext(), 10), 0);
        if (highlighted) line.setBackground(round(getContext(), secondary, 18));
        ImageView glyph = new ImageView(getContext());
        if (action == Action.BUILD_STICKER)
            glyph.setImageDrawable(new CompactGlyph(foreground, false));
        else glyph.setImageResource(icon);
        glyph.setScaleType(ImageView.ScaleType.FIT_CENTER);
        if (action != Action.BUILD_STICKER)
            glyph.setColorFilter(action == Action.DELETE ? danger : foreground);
        line.addView(glyph, new LayoutParams(dp(getContext(), 23), dp(getContext(), 23)));
        TextView title = new TextView(getContext());
        title.setText(name);
        title.setTextSize(15);
        title.setTextColor(action == Action.DELETE ? danger : foreground);
        title.setGravity(Gravity.CENTER_VERTICAL);
        LayoutParams textParams = new LayoutParams(0, -1, 1f);
        textParams.leftMargin = dp(getContext(), 14);
        line.addView(title, textParams);
        content.addView(line, new LayoutParams(-1, dp(getContext(), 48)));
        line.setContentDescription(name);
        line.setClickable(true);
        line.setFocusable(true);
        line.setOnClickListener(v -> {
            if (action == Action.BUILD_STICKER) {
                tab = TAB_STICKER;
                refresh();
            }
            dispatch(action);
        });
    }
    private void refresh() {
        tabs.removeAllViews();
        tabs.setVisibility(GONE);
        if (sendButton.getParent() instanceof android.view.ViewGroup)
            ((android.view.ViewGroup) sendButton.getParent()).removeView(sendButton);
        if (saveButton.getParent() instanceof android.view.ViewGroup)
            ((android.view.ViewGroup) saveButton.getParent()).removeView(saveButton);
        content.removeAllViews();
        if (tab == TAB_ACTIONS) {
            LinearLayout quick = new LinearLayout(getContext());
            quick.setOrientation(HORIZONTAL);
            addTile(quick, label(org.telegram.messenger.R.string.Reply),
                    org.telegram.messenger.R.drawable.msg_reply_small, Action.REPLY);
            addTile(quick, label(org.telegram.messenger.R.string.Copy),
                    org.telegram.messenger.R.drawable.msg_copy, Action.COPY);
            addTile(quick, label(org.telegram.messenger.R.string.Forward),
                    org.telegram.messenger.R.drawable.msg_forward, Action.FORWARD);
            addTile(quick, label(org.telegram.messenger.R.string.FlexyContextMore),
                    org.telegram.messenger.R.drawable.msg_forward, Action.MORE);
            content.addView(quick, new LayoutParams(-1, -2));
            View separator = new View(getContext());
            separator.setBackgroundColor(muted);
            separator.setAlpha(.18f);
            LayoutParams divider = new LayoutParams(-1, dp(getContext(), 1));
            divider.topMargin = dp(getContext(), 7);
            divider.bottomMargin = dp(getContext(), 5);
            content.addView(separator, divider);
            actionLine(label(org.telegram.messenger.R.string.PinToTop),
                    org.telegram.messenger.R.drawable.msg_pin, Action.PIN, false);
            actionLine(label(org.telegram.messenger.R.string.FlexyContextConvertSticker),
                    org.telegram.messenger.R.drawable.msg_edit, Action.BUILD_STICKER, true);
            actionLine(label(org.telegram.messenger.R.string.Delete),
                    org.telegram.messenger.R.drawable.msg_delete, Action.DELETE, false);
        } else if (tab == TAB_STICKER) {
            TextView back = button(label(org.telegram.messenger.R.string.FlexyContextActions), false);
            back.setOnClickListener(v -> { tab = TAB_ACTIONS; refresh(); });
            content.addView(back, new LayoutParams(-1, dp(getContext(), 38)));
            content.addView(stickerStatus, new LayoutParams(-1, dp(getContext(), 32)));
            LayoutParams preview = new LayoutParams(-1, dp(getContext(), 122));
            preview.topMargin = dp(getContext(), 4);
            content.addView(stickerPreview, preview);
            LinearLayout actions = new LinearLayout(getContext());
            actions.addView(sendButton, new LayoutParams(0, dp(getContext(), 45), 1f));
            LayoutParams save = new LayoutParams(0, dp(getContext(), 45), 1f);
            save.leftMargin = dp(getContext(), 6);
            actions.addView(saveButton, save);
            LayoutParams buttons = new LayoutParams(-1, dp(getContext(), 45));
            buttons.topMargin = dp(getContext(), 7);
            content.addView(actions, buttons);
        } else {
            // Native selection remains available from MORE; never a hidden no-op tile.
            tab = TAB_ACTIONS;
            refresh();
        }
    }

    private void cancelBounce() {
        if (bounce != null) bounce.cancel();
        bounce = null;
    }
    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        if (!BubbleInteractionSettings.springBounce(getContext())
                || !android.animation.ValueAnimator.areAnimatorsEnabled()) return;
        cancelBounce();
        setPivotY(0);
        bounce = new AnimatorSet();
        // Local four-keyframe elastic motion; does not intercept cell touches or native navigation.
        bounce.playTogether(
            ObjectAnimator.ofFloat(this, View.SCALE_X, .94f, 1.045f, .988f, 1f),
            ObjectAnimator.ofFloat(this, View.SCALE_Y, .94f, 1.045f, .988f, 1f),
            ObjectAnimator.ofFloat(this, View.TRANSLATION_Y, dp(getContext(), 8),
                    -dp(getContext(), 3), dp(getContext(), 1), 0f)
        );
        bounce.setDuration(270L);
        bounce.setInterpolator(new DecelerateInterpolator(1.05f));
        bounce.start();
    }
    @Override protected void onDetachedFromWindow() {
        cancelBounce();
        setScaleX(1f); setScaleY(1f); setTranslationY(0f);
        Runnable dispose=onDispose;onDispose=null;
        if(dispose!=null)dispose.run();
        clearStickerPreview();
        listener = null;
        super.onDetachedFromWindow();
    }
}
