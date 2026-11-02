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
    public float fusionTop;
    public float height, titlePx, subtitlePx;
    public boolean fusionActive() { return fusionLayout && HeaderConfig.fusion() && active(); }
    public app.flexygram.header.fusion.SignatureFusionGeometry.Layout fusionGeometry() { return fusion == null ? null : fusion.layout; }
    public boolean subtitleFits = true;
    public void detach() { bar.setSignatureHeader(null); avatar.setSignatureHeader(null); }
    public SignatureChatHeader(ActionBar bar, ChatAvatarContainer avatar, Theme.ResourcesProvider provider) {
        this.bar = bar; this.avatar = avatar; this.provider = provider;

    }
    private int unreadCount = 0;
    private android.text.StaticLayout unreadLayout;
    public boolean enabled() { return HeaderConfig.signature(); }
    public boolean active() { return enabled() && !bar.isSearchFieldVisible() && !bar.isActionModeShowed() && avatar.getVisibility() == View.VISIBLE; }
    /** Retained bridge for older callers; unread badges belong to the native chat list. */
    public void setCount(int value) {
        if (unreadCount != value) {
            unreadCount = value;
            if (value > 0) {
                String str = value > 99 ? "99+" : Integer.toString(value);
                int countWidth = (int) Math.ceil(Theme.dialogs_countTextPaint.measureText(str));
                unreadLayout = new android.text.StaticLayout(str, Theme.dialogs_countTextPaint, countWidth, android.text.Layout.Alignment.ALIGN_CENTER, 1.0f, 0.0f, false);
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
        if (HeaderConfig.fusion() && active()) {
            if (fusion == null) fusion = new Fusion();
            var g = HeaderConfig.portrait()
                    ? app.flexygram.header.fusion.SignatureFusionGeometry.updatePortrait(fusion.layout,
                        width, AndroidUtilities.density, LocaleController.isRTL, avatar.signatureCallAvailable())
                    : app.flexygram.header.fusion.SignatureFusionGeometry.update(fusion.layout,
                        width, AndroidUtilities.density, LocaleController.isRTL, avatar.signatureCallAvailable());
            // Keep the approved compact sizes; large fonts/narrow windows use the existing Adaptive path.
            if (g.fits && titleLine + subtitleLine + AndroidUtilities.dp(2) <= g.height - AndroidUtilities.dp(8)) {
                bar.prepareSignatureNativeGlass(g.mattePortrait && g.callAvailable);
                fusionLayout = true; height = g.height; subtitleFits = true;
                int content = Math.max(nativeHeight, Math.round(height) + AndroidUtilities.dp(12));
                fusionTop = status + (content - height) / 2f;
                geometry.back.set(g.back.left,g.back.top+fusionTop,g.back.right,g.back.bottom+fusionTop);
                geometry.title.set(g.text.left,g.text.top+fusionTop,g.text.right,g.text.bottom+fusionTop);
                geometry.avatar.set(g.portrait.left,g.portrait.top+fusionTop,g.portrait.right,g.portrait.bottom+fusionTop);
                geometry.countVisible = geometry.separateCount = false;
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
        float numberWidth = 0;
        int mode = HeaderConfig.counter() ? HeaderConfig.counterMode() : 0;
        if (mode != 0 && unreadCount > 0 && unreadLayout != null) {
            String str = unreadCount > 99 ? "99+" : Integer.toString(unreadCount);
            numberWidth = Theme.dialogs_countTextPaint.measureText(str);
        }
        geometry.update(width, status + (content - height) / 2f, height, numberWidth,
                AndroidUtilities.density, LocaleController.isRTL, mode, titleWidth);
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
        } else { bar.backButtonImageView.setPadding(AndroidUtilities.dp(1), 0, 0, 0); }
    }
    public void draw(Canvas canvas) {
        // Native Liquid Glass is a Telegram power-saving flag, not a new Flexy master switch.
        // Use the existing ActionBar blur3 sources only when they are ready.
        // Solid Signature rendering remains bit-for-bit unchanged when the flag is off.
        if (bar.drawSignatureNativeGlass(canvas, this)) return;
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
    private void drawUnread(Canvas canvas) {
        if (!geometry.countVisible || unreadLayout == null || unreadCount <= 0) return;
        canvas.save();
        int textColor = Theme.getColor(Theme.key_actionBarDefaultTitle, provider);
        Theme.dialogs_countTextPaint.setColor(textColor);
        if (geometry.separateCount) {
            canvas.translate(geometry.badge.centerX() - unreadLayout.getWidth() / 2f,
                    geometry.badge.centerY() - unreadLayout.getHeight() / 2f);
        } else {
            float textX = LocaleController.isRTL
                    ? geometry.back.left + AndroidUtilities.dp(8)
                    : geometry.back.right - unreadLayout.getWidth() - AndroidUtilities.dp(8);
            canvas.translate(textX, geometry.back.centerY() - unreadLayout.getHeight() / 2f);
        }
        unreadLayout.draw(canvas);
        canvas.restore();
    }
    /** One final center contour, after the real avatar; no double edge under the fading image. */
    public void drawForeground(Canvas canvas) {
        if (!fusionActive()) return;
        int border = (Theme.getColor(Theme.key_divider, provider) & 0xffffff) | 0x66000000;
        int save = canvas.save(); canvas.translate(0, fusionTop);
        fusion.surface.drawCenterBorder(canvas, fusion.layout, border, AndroidUtilities.density);
        canvas.restoreToCount(save);
    }
    private static int exact(float size) { return View.MeasureSpec.makeMeasureSpec(Math.max(0, Math.round(size)), View.MeasureSpec.EXACTLY); }
}
