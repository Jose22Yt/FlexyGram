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
import org.telegram.ui.ActionBar.Theme;

/**
 * Signature Matte 3-tab presentation only. Native ChatActivity owns all action
 * permissions and onClick outcomes. Never synthesizes clicks or sends messages.
 * Host must keep the selected MessageObject/peer and invalidate on detach.
 */
public final class BubbleActionPanelView extends LinearLayout {
    public enum Action { REPLY, COPY, FORWARD, EDIT, PIN, DELETE, SELECT, BUILD_STICKER, SEND_STICKER }
    public interface Listener { void onAction(Action action); }

    private static final int TAB_ACTIONS = 0, TAB_STICKER = 1, TAB_SELECT = 2;
    private final LinearLayout content;
    private final LinearLayout tabs;
    private final ImageView stickerPreview;
    private final TextView sendButton;
    private Listener listener;
    private int tab = TAB_ACTIONS;
    private boolean canSendSticker;
    private final int foreground, muted, accent, surface, secondary;
    private static int dp(Context c, float v) {
        return (int)(c.getResources().getDisplayMetrics().density * v + .5f);
    }
    public BubbleActionPanelView(Context context) {
        super(context);
        foreground = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);
        muted = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2);
        accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        surface = Theme.getColor(Theme.key_windowBackgroundWhite);
        secondary = Theme.getColor(Theme.key_windowBackgroundGray);
        setOrientation(VERTICAL);
        setPadding(dp(context, 10), dp(context, 10), dp(context, 10), dp(context, 12));
        setBackground(round(context, surface, 22));
        tabs = new LinearLayout(context);
        tabs.setOrientation(HORIZONTAL);
        addView(tabs, new LayoutParams(-1, dp(context, 48)));
        content = new LinearLayout(context);
        content.setOrientation(VERTICAL);
        LayoutParams contentLp = new LayoutParams(-1, -2);
        contentLp.topMargin = dp(context, 8);
        addView(content, contentLp);
        stickerPreview = new ImageView(context);
        stickerPreview.setScaleType(ImageView.ScaleType.FIT_CENTER);
        sendButton = button("Enviar aquí", true);
        sendButton.setEnabled(false);
        sendButton.setAlpha(.5f);
        sendButton.setOnClickListener(v -> dispatch(Action.SEND_STICKER));
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
        sendButton.setEnabled(canSendSticker);
        sendButton.setAlpha(canSendSticker ? 1f : .5f);
    }
    public void clearStickerPreview() { setStickerPreview(null); }
    private void dispatch(Action action) {
        if (listener != null) listener.onAction(action);
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
    private void addTile(LinearLayout row, String title, String symbol, Action action) {
        LinearLayout tile = new LinearLayout(getContext());
        tile.setGravity(Gravity.CENTER);
        tile.setOrientation(VERTICAL);
        tile.setBackground(round(getContext(), secondary, 13));
        TextView glyph = new TextView(getContext());
        glyph.setGravity(Gravity.CENTER);
        glyph.setText(symbol);
        glyph.setTextSize(22);
        glyph.setTextColor(action == Action.DELETE ? 0xffdc5555 : foreground);
        tile.addView(glyph, new LayoutParams(-1, dp(getContext(), 32)));
        TextView label = new TextView(getContext());
        label.setText(title);
        label.setTextSize(12);
        label.setTextColor(action == Action.DELETE ? 0xffdc5555 : foreground);
        label.setGravity(Gravity.CENTER);
        tile.addView(label, new LayoutParams(-1, dp(getContext(), 22)));
        LayoutParams p = new LayoutParams(0, dp(getContext(), 77), 1f);
        p.leftMargin = dp(getContext(), 3);
        p.rightMargin = dp(getContext(), 3);
        row.addView(tile, p);
        tile.setOnClickListener(v -> dispatch(action));
    }
    private void refresh() {
        tabs.removeAllViews();
        headerTab("Acciones", TAB_ACTIONS);
        headerTab("Sticker", TAB_STICKER);
        headerTab("Seleccionar", TAB_SELECT);
        content.removeAllViews();
        if (tab == TAB_ACTIONS) {
            LinearLayout one = new LinearLayout(getContext());
            addTile(one,"Responder","↩",Action.REPLY);
            addTile(one,"Copiar","▤",Action.COPY);
            addTile(one,"Reenviar","➜",Action.FORWARD);
            content.addView(one, new LayoutParams(-1,-2));
            LinearLayout two = new LinearLayout(getContext());
            addTile(two,"Editar","✎",Action.EDIT);
            addTile(two,"Fijar","♧",Action.PIN);
            addTile(two,"Eliminar","×",Action.DELETE);
            LayoutParams row = new LayoutParams(-1,-2);
            row.topMargin = dp(getContext(), 6);
            content.addView(two, row);
        } else if (tab == TAB_STICKER) {
            TextView info = button("Tu mensaje como sticker auténtico de Telegram", false);
            content.addView(info, new LayoutParams(-1, dp(getContext(), 40)));
            LayoutParams preview = new LayoutParams(-1, dp(getContext(), 142));
            preview.topMargin = dp(getContext(), 8);
            content.addView(stickerPreview, preview);
            LayoutParams send = new LayoutParams(-1, dp(getContext(), 45));
            send.topMargin = dp(getContext(), 8);
            content.addView(sendButton, send);
        } else {
            TextView select = button("Seleccionar mensaje", true);
            content.addView(select, new LayoutParams(-1, dp(getContext(), 52)));
            select.setOnClickListener(v -> dispatch(Action.SELECT));
        }
    }
    @Override protected void onDetachedFromWindow() {
        clearStickerPreview();
        listener = null;
        super.onDetachedFromWindow();
    }
}
