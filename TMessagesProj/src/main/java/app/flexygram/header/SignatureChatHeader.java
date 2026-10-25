package app.flexygram.header;

import android.graphics.Canvas;
import android.util.TypedValue;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.TextView;
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
    private final TextView countView;
    private int count = -1;
    private String number = "";
    public float height, titlePx, subtitlePx;
    public boolean subtitleFits = true;
    public void detach() { bar.setSignatureHeader(null); if (countView.getParent() == bar) bar.removeView(countView); }
    public SignatureChatHeader(ActionBar bar, ChatAvatarContainer avatar, Theme.ResourcesProvider provider) {
        this.bar = bar; this.avatar = avatar; this.provider = provider;
        countView = new TextView(bar.getContext()); countView.setTextSize(16); countView.setGravity(android.view.Gravity.CENTER);
        countView.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO); countView.setClickable(false); countView.setFocusable(false);
        bar.addView(countView, new FrameLayout.LayoutParams(0, 0));
    }
    public boolean enabled() { return HeaderConfig.signature(); }
    public boolean active() { return enabled() && !bar.isSearchFieldVisible() && !bar.isActionModeShowed() && avatar.getVisibility() == View.VISIBLE; }
    public void setCount(int value) {
        if (count == value) return;
        count = value; number = value < 0 ? "" : value > 999 ? "999+" : Integer.toString(value);
        countView.setText(number); changed();
    }
    public void changed() { avatar.requestLayout(); bar.requestLayout(); bar.invalidate(); }
    public int measure(int width, int status, int nativeHeight) {
        var metrics = bar.getResources().getDisplayMetrics();
        titlePx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 17.5f, metrics);
        subtitlePx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 13.5f, metrics);
        height = HeaderGeometry.height(width, titlePx, subtitlePx, AndroidUtilities.density, HeaderConfig.compact());
        subtitleFits = titlePx + subtitlePx + AndroidUtilities.dp(12) <= height;
        titlePx = Math.min(titlePx, height - AndroidUtilities.dp(8));
        int content = Math.max(nativeHeight, Math.round(height) + AndroidUtilities.dp(12));
        float digits = HeaderConfig.counter() && count >= 0 ? countView.getPaint().measureText(number) : 0;
        geometry.update(width, status + (content - height) / 2f, height, digits, AndroidUtilities.density, LocaleController.isRTL);
        return content;
    }
    public void measureControls() {
        if (bar.backButtonImageView == null) return;
        if (active()) {
            bar.backButtonImageView.measure(exact(geometry.back.width()), exact(height));
            countView.measure(exact(Math.max(0, geometry.back.width() - height)), exact(height));
        }
        countView.setVisibility(active() && geometry.countVisible ? View.VISIBLE : View.GONE);
    }
    public void layoutControls() {
        if (bar.backButtonImageView == null) return;
        if (active()) {
            var back = bar.backButtonImageView;
            back.setTranslationX(0);
            int extra = Math.round(geometry.back.width() - height);
            int pl = LocaleController.isRTL ? extra : 0, pr = LocaleController.isRTL ? 0 : extra;
            if (back.getPaddingLeft() != pl || back.getPaddingRight() != pr) back.setPadding(pl, 0, pr, 0);
            back.layout(Math.round(geometry.back.left), Math.round(geometry.back.top), Math.round(geometry.back.right), Math.round(geometry.back.bottom));
            float x = LocaleController.isRTL ? geometry.back.left : geometry.back.left + height;
            countView.layout(Math.round(x), Math.round(geometry.back.top), Math.round(x + extra), Math.round(geometry.back.bottom));
            back.setUnread(0);
            back.setContentDescription(LocaleController.getString(R.string.AccDescrGoBack) + (count >= 0 && HeaderConfig.counter() ? ", " + LocaleController.formatString(R.string.FlexyHeaderUnread, count) : ""));
            avatar.setTranslationX(0);
        } else { bar.backButtonImageView.setPadding(AndroidUtilities.dp(1), 0, 0, 0); }
        countView.setTextColor(Theme.getColor(Theme.key_actionBarDefaultTitle, provider));
    }
    public void draw(Canvas canvas) { surface.draw(canvas, geometry, AndroidUtilities.density, provider); }
    private static int exact(float size) { return View.MeasureSpec.makeMeasureSpec(Math.max(0, Math.round(size)), View.MeasureSpec.EXACTLY); }
}
