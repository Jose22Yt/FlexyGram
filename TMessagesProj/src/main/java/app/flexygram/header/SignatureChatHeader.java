package app.flexygram.header;

import android.graphics.Canvas;
import android.util.TypedValue;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.ChatAvatarContainer;

/** Presentation adapter only. Native back/profile/menu views continue to own navigation. */
public final class SignatureChatHeader {
    public final HeaderGeometry geometry = new HeaderGeometry();
    private final HeaderSurface surface = new HeaderSurface();
    private final ActionBar bar;
    private final ChatAvatarContainer avatar;
    private final Theme.ResourcesProvider provider;
    private final android.graphics.Paint textMetrics = new android.graphics.Paint();
    private final android.graphics.Paint.FontMetricsInt fontMetrics = new android.graphics.Paint.FontMetricsInt();
    private static final class Fusion {
        final app.flexygram.header.fusion.SignatureFusionGeometry.Layout layout = new app.flexygram.header.fusion.SignatureFusionGeometry.Layout();
        final app.flexygram.header.fusion.SignatureFusionSurface surface = new app.flexygram.header.fusion.SignatureFusionSurface();
    }
    private Fusion fusion;
    private boolean fusionLayout;
    private boolean nativeGlassDrawn;
    public float fusionTop;
    public float height, titlePx, subtitlePx;
    public boolean fusionActive() { return fusionLayout && HeaderConfig.fusion() && active(); }
    public app.flexygram.header.fusion.SignatureFusionGeometry.Layout fusionGeometry() { return fusion == null ? null : fusion.layout; }
    private final android.graphics.RectF badgeRect = new android.graphics.RectF();
    private final android.graphics.Paint badgePaint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    private final android.text.TextPaint unreadPaint = new android.text.TextPaint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    public boolean subtitleFits = true;
    public void detach() {
        if (bar != null && bar.getBackButtonDrawable() instanceof org.telegram.ui.ActionBar.BackDrawable) {
            ((org.telegram.ui.ActionBar.BackDrawable) bar.getBackButtonDrawable()).setIosStyle(false);
        }
        bar.setSignatureHeader(null);
        avatar.setSignatureHeader(null);
    }
    public SignatureChatHeader(ActionBar bar, ChatAvatarContainer avatar, Theme.ResourcesProvider provider) {
        this.bar = bar; this.avatar = avatar; this.provider = provider;
        if (bar != null && bar.getBackButtonDrawable() instanceof org.telegram.ui.ActionBar.BackDrawable) {
            ((org.telegram.ui.ActionBar.BackDrawable) bar.getBackButtonDrawable()).setIosStyle(enabled());
        }
    }
    private int unreadCount = 0;
    private android.text.StaticLayout unreadLayout;
    public boolean enabled() { return HeaderConfig.signature(); }
    public boolean active() { return enabled() && !bar.isSearchFieldVisible() && !bar.isActionModeShowed() && avatar.getVisibility() == View.VISIBLE; }
    /** Retained bridge for older callers; unread badges belong to the native chat list. */
    public void setCount(int value) {
        value = Math.max(0, value);
        int previousDisplay = Math.min(100, unreadCount);
        unreadCount = value;
        if (previousDisplay != Math.min(100, value)) {
            if (value > 0) {
                String str = value > 99 ? "99+" : Integer.toString(value);
                unreadPaint.set(Theme.dialogs_countTextPaint);
                int countWidth = (int) Math.ceil(unreadPaint.measureText(str));
                unreadLayout = new android.text.StaticLayout(str, unreadPaint, countWidth, android.text.Layout.Alignment.ALIGN_CENTER, 1.0f, 0.0f, false);
            } else {
                unreadLayout = null;
            }
            changed();
        }
    }
    public void changed() { avatar.requestLayout(); bar.requestLayout(); bar.invalidate(); }
    public int measure(int width, int status, int nativeHeight) {
        var metrics = bar.getResources().getDisplayMetrics();
        titlePx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, HeaderConfig.fusion() || HeaderConfig.compact() ? 16f : 17.5f, metrics);
        subtitlePx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 12f, metrics);
        textMetrics.setTextSize(titlePx); textMetrics.getFontMetricsInt(fontMetrics);
        int titleLine = fontMetrics.descent - fontMetrics.ascent;
        textMetrics.setTextSize(subtitlePx); textMetrics.getFontMetricsInt(fontMetrics);
        int subtitleLine = fontMetrics.descent - fontMetrics.ascent;
        fusionLayout = false;
        int mode = HeaderConfig.counter() ? HeaderConfig.counterMode() : 0;
        float numberWidth = mode != 0 && unreadCount > 0 && unreadLayout != null
                ? unreadLayout.getWidth() : 0;
        float countExtra = numberWidth <= 0 ? 0 : mode == 2
                ? Math.max(AndroidUtilities.dp(28), numberWidth + AndroidUtilities.dp(8)) + AndroidUtilities.dp(3)
                : numberWidth + AndroidUtilities.dp(16);
        if (HeaderConfig.fusion() && active()) {
            if (fusion == null) fusion = new Fusion();
            var g = HeaderConfig.floating()
                    ? app.flexygram.header.fusion.SignatureFusionGeometry.updateFloating(fusion.layout,
                        width, AndroidUtilities.density, LocaleController.isRTL, avatar.signatureCallAvailable(), countExtra)
                    : HeaderConfig.portrait()
                    ? app.flexygram.header.fusion.SignatureFusionGeometry.updatePortrait(fusion.layout,
                        width, AndroidUtilities.density, LocaleController.isRTL, avatar.signatureCallAvailable(), countExtra)
                    : app.flexygram.header.fusion.SignatureFusionGeometry.update(fusion.layout,
                        width, AndroidUtilities.density, LocaleController.isRTL, avatar.signatureCallAvailable(), countExtra);
            // Keep the approved compact sizes; large fonts/narrow windows use the existing Adaptive path.
            if (g.fits && (g.floatingStatus ? titleLine : titleLine + subtitleLine + AndroidUtilities.dp(2)) <= g.height - AndroidUtilities.dp(8)) {
                bar.prepareSignatureNativeGlass(g.mattePortrait && g.callAvailable);
                fusionLayout = true; height = g.height; subtitleFits = true;
                int extra = g.floatingStatus ? Math.round(
                        app.flexygram.header.fusion.SignatureFusionGeometry.statusHeight(
                                (float)Math.ceil(subtitlePx) + AndroidUtilities.dp(8), AndroidUtilities.density)) + AndroidUtilities.dp(8) : 0;
                int content = Math.max(nativeHeight, Math.round(height) + extra + AndroidUtilities.dp(12));
                fusionTop = status + (content - height - extra) / 2f;
                geometry.back.set(g.back.left,g.back.top+fusionTop,g.back.right,g.back.bottom+fusionTop);
                geometry.title.set(g.text.left,g.text.top+fusionTop,g.text.right,g.text.bottom+fusionTop);
                geometry.avatar.set(g.portrait.left,g.portrait.top+fusionTop,g.portrait.right,g.portrait.bottom+fusionTop);
                geometry.countVisible = numberWidth > 0;
                geometry.separateCount = numberWidth > 0 && mode == 2;
                app.flexygram.header.fusion.SignatureFusionGeometry.placeUnread(g, numberWidth, mode, AndroidUtilities.density);
                geometry.badge.set(g.unread.left,g.unread.top+fusionTop,g.unread.right,g.unread.bottom+fusionTop);
                bar.prepareSignatureUnreadGlass(geometry.separateCount);
                return content;
            }
        }
        height = HeaderGeometry.height(width, titleLine, subtitleLine, AndroidUtilities.density, HeaderConfig.compact());
        // Narrow windows cap side geometry; retain both lines by fitting the text block together.
        float fit = Math.min(1f, (height - AndroidUtilities.dp(8)) / (titleLine + subtitleLine));
        titlePx *= fit; subtitlePx *= fit;
        subtitleFits = true;
        titlePx = Math.min(titlePx, height - AndroidUtilities.dp(8));
        int content = Math.max(nativeHeight, Math.round(height) + AndroidUtilities.dp(12));
        float titleWidth = avatar.signaturePreferredTitleWidth(titlePx, subtitlePx, textMetrics);
        geometry.update(width, status + (content - height) / 2f, height, numberWidth,
                AndroidUtilities.density, LocaleController.isRTL, mode, titleWidth);
        bar.prepareSignatureUnreadGlass(geometry.separateCount);
        return content;
    }
    public void measureControls() {
        if (bar.backButtonImageView == null) return;
        if (active()) {
            bar.backButtonImageView.measure(exact(Math.max(AndroidUtilities.dp(48), geometry.back.width())), exact(Math.max(AndroidUtilities.dp(48), fusionActive() ? geometry.back.height() : height)));
        }
    }
    public void layoutControls() {
        if (bar.backButtonImageView == null) return;
        if (active()) {
            var back = bar.backButtonImageView;
            if (bar.getBackButtonDrawable() instanceof org.telegram.ui.ActionBar.BackDrawable) {
                ((org.telegram.ui.ActionBar.BackDrawable) bar.getBackButtonDrawable()).setIosStyle(true);
            }
            back.setTranslationX(0);
            int extra = Math.round(geometry.back.width() - (fusionActive() ? geometry.back.height() : height));
            int pl = LocaleController.isRTL ? extra : 0, pr = LocaleController.isRTL ? 0 : extra;
            if (back.getPaddingLeft() != pl || back.getPaddingRight() != pr) back.setPadding(pl, 0, pr, 0);
            int hitLeft = Math.round(geometry.back.centerX() - back.getMeasuredWidth() / 2f);
            int hitTop = Math.round(geometry.back.centerY() - back.getMeasuredHeight() / 2f);
            back.layout(hitLeft, hitTop, hitLeft + back.getMeasuredWidth(), hitTop + back.getMeasuredHeight());
            back.setUnread(0);
            back.setContentDescription(LocaleController.getString(R.string.AccDescrGoBack));
            avatar.setTranslationX(0);
        } else {
            if (bar.getBackButtonDrawable() instanceof org.telegram.ui.ActionBar.BackDrawable) {
                ((org.telegram.ui.ActionBar.BackDrawable) bar.getBackButtonDrawable()).setIosStyle(false);
            }
            bar.backButtonImageView.setPadding(AndroidUtilities.dp(1), 0, 0, 0);
        }
    }
    public void draw(Canvas canvas) {
        // Native Liquid Glass is a Telegram power-saving flag, not a new Flexy master switch.
        // Use the existing ActionBar blur3 sources only when they are ready.
        // Solid Signature rendering remains bit-for-bit unchanged when the flag is off.
        nativeGlassDrawn = bar.drawSignatureNativeGlass(canvas, this);
        if (nativeGlassDrawn) {
            drawUnread(canvas);
            return;
        }
        if (!fusionActive()) {
            surface.draw(canvas, geometry, AndroidUtilities.density, provider);
            drawUnread(canvas);
            return;
        }
        int fill = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
        fill = (fill & 0xffffff) | ((HeaderConfig.portrait() ? 255 : Math.round(HeaderConfig.opacity() * 2.55f)) << 24);
        int border = (Theme.getColor(Theme.key_divider, provider) & 0xffffff) | 0x66000000;
        int save = canvas.save(); canvas.translate(0, fusionTop);
        fusion.surface.drawBackdrop(canvas, fusion.layout, fill, border, border, AndroidUtilities.density);
        canvas.restoreToCount(save);
        drawUnread(canvas);
    }
    public void drawStatusBackground(Canvas canvas) {
        if (!fusionActive() || !fusion.layout.floatingStatus) return;
        int fill = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
        fill = (fill & 0xffffff) | (Math.round(HeaderConfig.opacity() * 2.55f) << 24);
        int edge = (Theme.getColor(Theme.key_actionBarDefaultSubtitle, provider) & 0xffffff) | 0x38000000;
        int save = canvas.save();
        canvas.translate(0, fusionTop);
        fusion.surface.drawStatus(canvas, fusion.layout, fill, edge, AndroidUtilities.density);
        canvas.restoreToCount(save);
    }
    private int lastBadgeAccent;
    private int badgeTextColor;
    private boolean badgeColorsReady;

    private void drawUnread(Canvas canvas) {
        if (!geometry.countVisible || unreadLayout == null || unreadCount <= 0) return;
        canvas.save();
        int accent = androidx.core.graphics.ColorUtils.setAlphaComponent(Theme.getColor(Theme.key_telegram_color, provider), 255);
        if (!badgeColorsReady || lastBadgeAccent != accent) {
            badgeColorsReady = true;
            lastBadgeAccent = accent;
            badgePaint.setColor(accent);
            badgeTextColor = androidx.core.graphics.ColorUtils.calculateContrast(android.graphics.Color.WHITE, accent)
                    >= androidx.core.graphics.ColorUtils.calculateContrast(android.graphics.Color.BLACK, accent)
                    ? android.graphics.Color.WHITE : android.graphics.Color.BLACK;
        }
        unreadPaint.setColor(badgeTextColor);

        float badgeHeight = AndroidUtilities.dp(23);
        float badgeRadius = badgeHeight / 2f;
        float textWidth = unreadLayout.getWidth();
        float badgePadH = AndroidUtilities.dp(6);
        float badgeWidth = Math.max(badgeHeight, textWidth + badgePadH * 2);

        if (geometry.separateCount) {
            badgeRect.set(geometry.badge.centerX() - badgeWidth / 2f,
                    geometry.badge.centerY() - badgeHeight / 2f,
                    geometry.badge.centerX() + badgeWidth / 2f,
                    geometry.badge.centerY() + badgeHeight / 2f);
        } else {
            float margin = AndroidUtilities.dp(7);
            if (LocaleController.isRTL) {
                float left = geometry.back.left + margin;
                badgeRect.set(left, geometry.back.centerY() - badgeHeight / 2f,
                        left + badgeWidth, geometry.back.centerY() + badgeHeight / 2f);
            } else {
                float right = geometry.back.right - margin;
                badgeRect.set(right - badgeWidth, geometry.back.centerY() - badgeHeight / 2f,
                        right, geometry.back.centerY() + badgeHeight / 2f);
            }
        }
        canvas.drawRoundRect(badgeRect, badgeRadius, badgeRadius, badgePaint);

        canvas.translate(badgeRect.centerX() - textWidth / 2f,
                badgeRect.centerY() - unreadLayout.getHeight() / 2f);
        unreadLayout.draw(canvas);
        canvas.restore();
    }
    /** One final center contour, after the real avatar; no double edge under the fading image. */
    public void drawForeground(Canvas canvas) {
        if (!fusionActive() || nativeGlassDrawn) return;
        int border = (Theme.getColor(Theme.key_divider, provider) & 0xffffff) | 0x66000000;
        int save = canvas.save(); canvas.translate(0, fusionTop);
        fusion.surface.drawCenterBorder(canvas, fusion.layout, border, AndroidUtilities.density);
        canvas.restoreToCount(save);
    }
    private static int exact(float size) { return View.MeasureSpec.makeMeasureSpec(Math.max(0, Math.round(size)), View.MeasureSpec.EXACTLY); }
}
