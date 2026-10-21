package org.telegram.ui.beta;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Account-free demo content. Only framework widgets and fixed local text.
 * No MessageObject/ChatMessageCell, Telegram controllers, emoji loaders or native/Python calls.
 * This is an offline fixture, not a replacement for authenticated chat rendering.
 */
final class OfflineConversationView extends ScrollView {
    private static final String[] TEXT = {
        "Esta conversación es una demostración local.",
        "Puedo abrirla y volver sin iniciar sesión.",
        "Prueba Atrás y los toques consecutivos. No se envía ningún mensaje."
    };

    OfflineConversationView(Context context, boolean dark) {
        super(context);
        setFillViewport(true);
        setBackgroundColor(dark ? 0xff101820 : 0xffedf2f5);
        DisplayMetrics metrics = context.getResources().getDisplayMetrics();
        float density = metrics.density > 0 && metrics.density <= 10 ? metrics.density : 1;
        int gap = Math.max(1, Math.round(12 * density));
        int maxWidth = Math.max(1, Math.round((metrics.widthPixels > 0
                ? metrics.widthPixels : 320 * density) * .78f));
        LinearLayout messages = new LinearLayout(context);
        messages.setOrientation(LinearLayout.VERTICAL);
        messages.setPadding(gap, gap, gap, gap);
        for (int index = 0; index < TEXT.length; index++) {
            boolean outgoing = index == 1;
            LinearLayout row = new LinearLayout(context);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(outgoing ? Gravity.END : Gravity.START);
            row.setPadding(0, gap / 2, 0, gap / 2);
            LinearLayout bubble = new LinearLayout(context);
            bubble.setOrientation(LinearLayout.VERTICAL);
            bubble.setPadding(gap, gap * 3 / 4, gap, gap * 3 / 4);
            GradientDrawable background = new GradientDrawable();
            background.setColor(outgoing ? (dark ? 0xff294858 : 0xffdcebf1)
                    : (dark ? 0xff22303a : 0xffffffff));
            background.setCornerRadius(16 * density);
            bubble.setBackground(background);
            TextView text = new TextView(context);
            text.setText(TEXT[index]);
            text.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
            text.setTextColor(dark ? 0xfff1f5f8 : 0xff17242d);
            text.setMaxWidth(maxWidth);
            bubble.addView(text);
            TextView stamp = new TextView(context);
            stamp.setText(outgoing ? "10:01 · Local" : "10:00 · Local");
            stamp.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
            stamp.setTextColor(dark ? 0xffafc3ce : 0xff536b78);
            stamp.setGravity(Gravity.END);
            bubble.addView(stamp);
            row.addView(bubble);
            messages.addView(row, new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        }
        addView(messages, new ScrollView.LayoutParams(
                ScrollView.LayoutParams.MATCH_PARENT, ScrollView.LayoutParams.WRAP_CONTENT));
    }
}
