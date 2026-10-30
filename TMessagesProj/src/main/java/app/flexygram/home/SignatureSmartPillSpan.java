/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.text.TextPaint;
import android.text.style.ReplacementSpan;
import androidx.annotation.NonNull;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/**
 * In-line badge with its own measured width. Never paints over the filename or
 * next to the chat's time/unread indicators: the native StaticLayout reserves its
 * horizontal space before ellipsizing the remaining snippet.
 */
public final class SignatureSmartPillSpan extends ReplacementSpan {
    private final String label;
    private final int kind;
    private final Theme.ResourcesProvider resourcesProvider;
    private final SignatureSmartPreviewPalette colors = new SignatureSmartPreviewPalette();
    private final TextPaint ink = new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private int measured;
    private float width;
    private float height;
    private float leftPadding;

    public SignatureSmartPillSpan(int kind, String label, Theme.ResourcesProvider resourcesProvider) {
        this.kind = kind;
        this.label = label == null ? "" : label;
        this.resourcesProvider = resourcesProvider;
    }

    @Override
    public int getSize(@NonNull Paint paint, CharSequence text, int start, int end, Paint.FontMetricsInt fm) {
        // Do not change fm: row height/line baseline and clickable bounds stay native.
        ink.setTypeface(paint.getTypeface());
        ink.setTextSize(Math.max(AndroidUtilities.dp(10), Math.min(AndroidUtilities.dp(12), paint.getTextSize() * .78f)));
        width = ink.measureText(label);
        leftPadding = AndroidUtilities.dp(6);
        height = Math.min(AndroidUtilities.dp(20), Math.max(AndroidUtilities.dp(17), paint.getTextSize() * 1.08f));
        measured = (int) Math.ceil(width + leftPadding * 2);
        return measured;
    }

    @Override
    public void draw(@NonNull Canvas canvas, CharSequence text, int start, int end,
                     float x, int top, int y, int bottom, @NonNull Paint paint) {
        if (measured <= 0) getSize(paint, text, start, end, null);
        int mode = SignatureSmartPreviews.mode();
        if (mode == SignatureSmartPreviewPalette.OFF) return;
        colors.update(kind, mode,
                Theme.getColor(Theme.key_actionBarTabLine, resourcesProvider),
                Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));
        int alpha = paint.getAlpha();
        float centerY = (top + bottom) * .5f;
        fill.setColor(colors.background());
        fill.setAlpha(alpha);
        float radius = height * .5f;
        canvas.drawRoundRect(x, centerY - radius, x + measured,
                centerY + radius, radius, radius, fill);
        ink.setColor(colors.foreground());
        ink.setAlpha(alpha);
        float textBaseline = centerY - (ink.ascent() + ink.descent()) * .5f;
        canvas.drawText(label, x + leftPadding, textBaseline, ink);
    }

    public String label() { return label; }
}
