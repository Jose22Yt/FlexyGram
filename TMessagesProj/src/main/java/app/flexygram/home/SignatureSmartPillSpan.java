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
    private final int kind;
    private final String snippet;
    private final int maxAvailableWidth;
    private final Theme.ResourcesProvider resourcesProvider;
    private final boolean isDocument;
    private final SignatureSmartPreviewPalette colors = new SignatureSmartPreviewPalette();
    private final TextPaint ink = new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint iconPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private int measured;
    private float height;
    private float iconSize;
    private float iconSpacing;
    private float paddingH;
    private String displayText;

    public SignatureSmartPillSpan(int kind, String snippet, int maxAvailableWidth,
                                  Theme.ResourcesProvider resourcesProvider, boolean isDocument) {
        this.kind = kind;
        this.snippet = snippet == null ? "" : snippet;
        this.maxAvailableWidth = maxAvailableWidth;
        this.resourcesProvider = resourcesProvider;
        this.isDocument = isDocument;
        this.displayText = this.snippet;
    }

    public SignatureSmartPillSpan(int kind, String label, Theme.ResourcesProvider resourcesProvider) {
        this(kind, label, 0, resourcesProvider, false);
    }

    @Override
    public int getSize(@NonNull Paint paint, CharSequence text, int start, int end, Paint.FontMetricsInt fm) {
        // Row height / line baseline stays native.
        try {
            ink.setTypeface(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        } catch (Exception ignore) {
            ink.setTypeface(paint.getTypeface());
        }
        ink.setTextSize(Math.max(AndroidUtilities.dp(10f), Math.min(AndroidUtilities.dp(11.5f), paint.getTextSize() * 0.74f)));

        height = AndroidUtilities.dp(20f);
        iconSize = AndroidUtilities.dp(12f);
        iconSpacing = AndroidUtilities.dp(3.5f);
        paddingH = AndroidUtilities.dp(6f);

        displayText = snippet;
        float textWidth = ink.measureText(displayText);
        float neededWidth = paddingH * 2 + iconSize + iconSpacing + textWidth;
        if (maxAvailableWidth > 0 && neededWidth > maxAvailableWidth) {
            float textBudget = Math.max(AndroidUtilities.dp(20f), maxAvailableWidth - (paddingH * 2 + iconSize + iconSpacing));
            displayText = android.text.TextUtils.ellipsize(snippet, ink, textBudget,
                    isDocument ? android.text.TextUtils.TruncateAt.MIDDLE : android.text.TextUtils.TruncateAt.END).toString();
            textWidth = ink.measureText(displayText);
            neededWidth = paddingH * 2 + iconSize + iconSpacing + textWidth;
        }
        measured = (int) Math.ceil(neededWidth);
        return measured;
    }

    @Override
    public void draw(@NonNull Canvas canvas, CharSequence text, int start, int end,
                     float x, int top, int y, int bottom, @NonNull Paint paint) {
        if (measured <= 0) getSize(paint, text, start, end, null);
        int mode = SignatureSmartPreviews.mode();
        if (mode == SignatureSmartPreviewPalette.OFF) return;

        int accent = Theme.getColor(Theme.key_actionBarTabLine, resourcesProvider);
        int surface = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
        colors.update(kind, mode, accent, surface);

        int alpha = paint.getAlpha();
        float centerY = (top + bottom) * 0.5f;

        // 1. Draw capsule background
        fill.setColor(colors.background());
        fill.setAlpha(alpha);
        float radius = height * 0.5f;
        canvas.drawRoundRect(x, centerY - radius, x + measured, centerY + radius, radius, radius, fill);

        // 2. Draw icon
        iconPaint.setColor(colors.iconColor());
        iconPaint.setAlpha(alpha);
        int iconType = SignatureSmartPreviews.iconKind(kind);
        SignaturePreviewIcon.draw(canvas, iconType, x + paddingH, centerY - iconSize * 0.5f, iconSize, iconPaint);

        // 3. Draw text
        ink.setColor(colors.foreground());
        ink.setAlpha(alpha);
        float textX = x + paddingH + iconSize + iconSpacing;
        float textBaseline = centerY - (ink.ascent() + ink.descent()) * 0.5f;
        canvas.drawText(displayText, textX, textBaseline, ink);
    }

    public String label() {
        return displayText != null ? displayText : snippet;
    }
}
