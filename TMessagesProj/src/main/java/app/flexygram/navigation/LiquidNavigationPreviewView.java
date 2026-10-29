/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.MotionEvent;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.ActionBar.Theme;
import tw.nekomimi.nekogram.helpers.MainTabsHelper;
import app.exteraless.appearance.AppearanceConfig;

/** Interactive settings preview; real tabs use MainTabsLayout and native fragment routes. */
public final class LiquidNavigationPreviewView extends View {
    private final Paint background = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint liquid = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint labelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF bar = new RectF(), indicator = new RectF();
    private final int[] labels = {R.string.MainTabsChats, R.string.MainTabsContacts,
            R.string.MainTabsCalls, R.string.Settings, R.string.MainTabsProfile, R.string.Feed};
    private final int[] selectedLabels = new int[6];
    private int count, current;
    private float fingerX, lastX, deformation;
    private boolean touching;

    public LiquidNavigationPreviewView(Context context) {
        super(context);
        setClickable(true);
        setFocusable(true);
        setContentDescription(context.getString(R.string.FlexyLiquidNavPreview));
    }
    public void settingsChanged() { invalidate(); }
    @Override protected void onMeasure(int w, int h) {
        setMeasuredDimension(MeasureSpec.getSize(w), AndroidUtilities.dp(115));
    }
    private void rebuild() {
        count = 0;
        selectedLabels[count++] = labels[0]; // Chats cannot disappear.
        if (AppearanceConfig.showFeedTab()) selectedLabels[count++] = labels[5];
        else if (!MainTabsHelper.isContactsTabHidden()) selectedLabels[count++] = labels[1];
        selectedLabels[count++] = MainTabsHelper.isCallsTabShown(UserConfig.selectedAccount)
                ? labels[2] : labels[3];
        if (!MainTabsHelper.isProfileTabHidden()) selectedLabels[count++] = labels[4];
        current = Math.min(current, count - 1);
    }
    @Override protected void onDraw(Canvas canvas) {
        rebuild();
        final float d = AndroidUtilities.density;
        bar.set(AndroidUtilities.dp(14), AndroidUtilities.dp(26),
                getWidth() - AndroidUtilities.dp(14), AndroidUtilities.dp(90));
        background.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        canvas.drawRoundRect(bar, bar.height() * .5f, bar.height() * .5f, background);
        final float width = bar.width() / count;
        final float center = touching
                ? LiquidNavigationMath.center(fingerX, bar.left + width * .5f, bar.right - width * .5f)
                : bar.left + width * (current + .5f);
        final float visualWidth = LiquidNavigationMath.width(width - 5 * d, deformation);
        final float height = bar.height() - AndroidUtilities.dp(9);
        indicator.set(center - visualWidth * .5f, bar.centerY() - height * .5f,
                center + visualWidth * .5f, bar.centerY() + height * .5f);
        liquid.setColor(Theme.multAlpha(Theme.getColor(Theme.key_glass_tabSelected),
                LiquidNavigationConfig.opacity() / 100f));
        canvas.drawRoundRect(indicator, height * .5f, height * .5f, liquid);
        labelPaint.setTextAlign(Paint.Align.CENTER);
        labelPaint.setTextSize(AndroidUtilities.dp(count > 4 ? 9 : 11));
        labelPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        for (int i = 0; i < count; i++) {
            final String label = getContext().getString(selectedLabels[i]);
            final String clipped = label.length() > 10 && count > 3
                    ? label.substring(0, 9) + "…" : label;
            canvas.drawText(clipped, bar.left + width * (i + .5f),
                    bar.centerY() + AndroidUtilities.dp(4), labelPaint);
        }
    }
    @Override public boolean onTouchEvent(MotionEvent event) {
        final int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            if (event.getY() < AndroidUtilities.dp(12) || event.getY() > AndroidUtilities.dp(100))
                return false;
            touching = true; fingerX = lastX = event.getX(); deformation = 0;
            invalidate();
            return true;
        } else if (action == MotionEvent.ACTION_MOVE && touching) {
            fingerX = event.getX();
            deformation = LiquidNavigationMath.stretch(fingerX - lastX,
                    Math.max(1f, bar.width() / Math.max(1, count)), LiquidNavigationConfig.elasticity());
            lastX = fingerX; invalidate();
            return true;
        } else if ((action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL)
                && touching) {
            if (action == MotionEvent.ACTION_UP) {
                final float x = LiquidNavigationMath.center(event.getX(), bar.left, bar.right);
                current = Math.max(0, Math.min(count - 1,
                        (int) ((x - bar.left) / Math.max(1f, bar.width() / count))));
                performClick();
            }
            touching = false; deformation = 0; invalidate();
            return true;
        }
        return super.onTouchEvent(event);
    }
    @Override public boolean performClick() { super.performClick(); return true; }
}
