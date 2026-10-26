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
    public float height, titlePx, subtitlePx;
    public boolean subtitleFits = true;
    public void detach() { bar.setSignatureHeader(null); }
    public SignatureChatHeader(ActionBar bar, ChatAvatarContainer avatar, Theme.ResourcesProvider provider) {
        this.bar = bar; this.avatar = avatar; this.provider = provider;

    }
    public boolean enabled() { return HeaderConfig.signature(); }
    public boolean active() { return enabled() && !bar.isSearchFieldVisible() && !bar.isActionModeShowed() && avatar.getVisibility() == View.VISIBLE; }
    /** Retained bridge for older callers; unread badges belong to the native chat list. */
    public void setCount(int value) { }
    public void changed() { avatar.requestLayout(); bar.requestLayout(); bar.invalidate(); }
    public int measure(int width, int status, int nativeHeight) {
        var metrics = bar.getResources().getDisplayMetrics();
        titlePx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, HeaderConfig.compact() ? 16f : 17.5f, metrics);
        subtitlePx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, HeaderConfig.compact() ? 12f : 13.5f, metrics);
        textMetrics.setTextSize(titlePx); textMetrics.getFontMetricsInt(fontMetrics);
        int titleLine = fontMetrics.descent - fontMetrics.ascent;
        textMetrics.setTextSize(subtitlePx); textMetrics.getFontMetricsInt(fontMetrics);
        int subtitleLine = fontMetrics.descent - fontMetrics.ascent;
        height = HeaderGeometry.height(width, titleLine, subtitleLine, AndroidUtilities.density, HeaderConfig.compact());
        // Narrow windows cap side geometry; retain both lines by fitting the text block together.
        float fit = Math.min(1f, (height - AndroidUtilities.dp(8)) / (titleLine + subtitleLine));
        titlePx *= fit; subtitlePx *= fit;
        subtitleFits = true;
        titlePx = Math.min(titlePx, height - AndroidUtilities.dp(8));
        int content = Math.max(nativeHeight, Math.round(height) + AndroidUtilities.dp(12));
        float titleWidth = avatar.signaturePreferredTitleWidth(titlePx, subtitlePx, textMetrics);
        geometry.update(width, status + (content - height) / 2f, height, 0,
                AndroidUtilities.density, LocaleController.isRTL, 0, titleWidth);
        return content;
    }
    public void measureControls() {
        if (bar.backButtonImageView == null) return;
        if (active()) {
            bar.backButtonImageView.measure(exact(Math.max(AndroidUtilities.dp(48), geometry.back.width())), exact(Math.max(AndroidUtilities.dp(48), height)));
        }
    }
    public void layoutControls() {
        if (bar.backButtonImageView == null) return;
        if (active()) {
            var back = bar.backButtonImageView;
            back.setTranslationX(0);
            int extra = Math.round(geometry.back.width() - height);
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
    public void draw(Canvas canvas) { surface.draw(canvas, geometry, AndroidUtilities.density, provider); }
    private static int exact(float size) { return View.MeasureSpec.makeMeasureSpec(Math.max(0, Math.round(size)), View.MeasureSpec.EXACTLY); }
}
