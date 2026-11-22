package app.flexygram.notifications;

import static org.telegram.messenger.AndroidUtilities.dp;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.VelocityTracker;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.accessibility.AccessibilityManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.core.view.DisplayCutoutCompat;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.accessibility.AccessibilityNodeInfoCompat;

import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.CubicBezierInterpolator;

final class InAppBannerView extends FrameLayout {
    private final LinearLayout capsule;
    private final TextView title, preview;
    private final GradientDrawable background = new GradientDrawable();
    private final Runnable expire = this::dismiss;
    private final int touchSlop;
    private final int[] location = new int[2];
    private ValueAnimator animator;
    private VelocityTracker velocity;
    private Runnable action;
    private float progress, anchorX, anchorY, anchorWidth, downY, downX, downProgress, dragDistance;
    private boolean dragging, cancelled, closing;

    InAppBannerView(Context context) {
        super(context);
        touchSlop = ViewConfiguration.get(context).getScaledTouchSlop();
        capsule = new LinearLayout(context);
        capsule.setOrientation(LinearLayout.VERTICAL);
        capsule.setGravity(Gravity.CENTER_VERTICAL);
        capsule.setPadding(dp(16), dp(8), dp(16), dp(8));
        capsule.setMinimumHeight(dp(56));
        capsule.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        title = new TextView(context);
        title.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        title.setTextSize(15);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setMaxLines(1);
        title.setEllipsize(TextUtils.TruncateAt.END);
        preview = new TextView(context);
        preview.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        preview.setTextSize(14);
        preview.setMaxLines(2);
        preview.setEllipsize(TextUtils.TruncateAt.END);
        background.setCornerRadius(dp(22));
        capsule.setBackground(background);
        capsule.addView(title);
        capsule.addView(preview);
        capsule.setOnClickListener(v -> open());
        capsule.setOnTouchListener(this::touch);
        ViewCompat.replaceAccessibilityAction(capsule,
                AccessibilityNodeInfoCompat.AccessibilityActionCompat.ACTION_DISMISS,
                LocaleController.getString(R.string.FlexyInAppAlertDismiss), (v, arguments) -> {
                    dismiss();
                    return true;
                });
        addView(capsule, new LayoutParams(0, LayoutParams.WRAP_CONTENT, Gravity.TOP | Gravity.CENTER_HORIZONTAL));
        setOnApplyWindowInsetsListener((v, insets) -> {
            place(WindowInsetsCompat.toWindowInsetsCompat(insets, v), getWidth());
            return insets;
        });
        setVisibility(GONE);
    }

    @Override
    protected void onDetachedFromWindow() {
        hide();
        super.onDetachedFromWindow();
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        place(ViewCompat.getRootWindowInsets(this), w);
    }

    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        super.onLayout(changed, left, top, right, bottom);
        applyProgress();
    }

    private void place(WindowInsetsCompat insets, int width) {
        if (width <= 0) return;
        androidx.core.graphics.Insets safe = insets == null ? androidx.core.graphics.Insets.NONE :
                insets.getInsets(WindowInsetsCompat.Type.statusBars() | WindowInsetsCompat.Type.displayCutout());
        final int top = Math.max(org.telegram.messenger.AndroidUtilities.statusBarHeight, safe.top) + dp(6);
        anchorX = width / 2f;
        anchorY = -dp(32);
        anchorWidth = dp(28);
        DisplayCutoutCompat cutout = insets == null ? null : insets.getDisplayCutout();
        View parent = (View) getParent();
        if (cutout != null && parent != null && parent.getHeight() > width) {
            getLocationInWindow(location);
            for (Rect rect : cutout.getBoundingRects()) {
                int x = rect.centerX() - location[0];
                int y = rect.centerY() - location[1];
                if (isCameraCutout(rect, x, y, width, top)) {
                    anchorX = x;
                    anchorY = y;
                    anchorWidth = rect.width();
                    break;
                }
            }
        }
        LayoutParams params = (LayoutParams) capsule.getLayoutParams();
        int side = dp(12) + Math.max(safe.left, safe.right);
        int capsuleWidth = Math.max(1, Math.min(dp(410), width - 2 * side));
        if (params.width != capsuleWidth || params.topMargin != top) {
            params.width = capsuleWidth;
            params.topMargin = top;
            capsule.setLayoutParams(params);
        }
        applyProgress();
    }

    private static boolean isCameraCutout(Rect rect, int x, int y, int width, int top) {
        return x > 0 && x < width && y >= 0 && y < top && rect.width() >= dp(4)
                && rect.width() <= dp(32) && rect.height() > 0
                && rect.width() * 3 >= rect.height() * 2
                && rect.height() * 3 >= rect.width() * 2;
    }

    void show(CharSequence name, CharSequence text, Runnable open, boolean update) {
        title.setText(name);
        preview.setText(text);
        preview.setVisibility(TextUtils.isEmpty(text) ? GONE : VISIBLE);
        capsule.setContentDescription(TextUtils.isEmpty(text) ? name : TextUtils.concat(name, "\n", text));
        action = open;
        if (update && !closing && getVisibility() == VISIBLE) {
            if (velocity == null) scheduleExpiry();
            return;
        }
        stopAnimation();
        clearTouch();
        removeCallbacks(expire);
        closing = false;
        background.setColor(Theme.getColor(Theme.key_windowBackgroundWhite) | Color.BLACK);
        background.setStroke(dp(1), Theme.getColor(Theme.key_divider));
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        preview.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        setVisibility(VISIBLE);
        View parent = (View) getParent();
        place(ViewCompat.getRootWindowInsets(this), parent.getWidth());
        progress = 0f;
        applyProgress();
        animateTo(1f);
    }

    private void open() {
        if (closing) return;
        Runnable selected = action;
        hide();
        if (selected != null) selected.run();
    }

    private void scheduleExpiry() {
        removeCallbacks(expire);
        int duration = 4200;
        if (Build.VERSION.SDK_INT >= 29) {
            AccessibilityManager manager = getContext().getSystemService(AccessibilityManager.class);
            if (manager != null) duration = manager.getRecommendedTimeoutMillis(duration,
                    AccessibilityManager.FLAG_CONTENT_TEXT | AccessibilityManager.FLAG_CONTENT_CONTROLS);
        }
        postDelayed(expire, duration);
    }

    private void animateTo(float target) {
        stopAnimation();
        if ((Build.VERSION.SDK_INT >= 26 && !ValueAnimator.areAnimatorsEnabled()) || target == progress) {
            progress = target;
            applyProgress();
            finishMotion(target);
            return;
        }
        animator = ValueAnimator.ofFloat(progress, target);
        animator.setDuration(100 + (int) (140 * Math.abs(target - progress)));
        animator.setInterpolator(CubicBezierInterpolator.EASE_OUT_QUINT);
        animator.addUpdateListener(value -> {
            progress = (float) value.getAnimatedValue();
            applyProgress();
        });
        animator.addListener(new android.animation.AnimatorListenerAdapter() {
            @Override
            public void onAnimationEnd(android.animation.Animator animation) {
                if (animator != animation) return;
                animator = null;
                finishMotion(target);
            }
        });
        animator.start();
    }

    private void finishMotion(float target) {
        if (target == 0f) hide();
        else if (velocity == null) scheduleExpiry();
    }

    private void applyProgress() {
        float startScale = Math.min(0.4f, anchorWidth / Math.max(1, capsule.getWidth()));
        float scale = startScale + (1f - startScale) * progress;
        capsule.setScaleX(scale);
        capsule.setScaleY(scale);
        capsule.setTranslationX((anchorX - getWidth() / 2f) * (1f - progress));
        capsule.setTranslationY((anchorY - capsule.getTop() - capsule.getHeight() / 2f) * (1f - progress));
        capsule.setAlpha(Math.min(1f, progress * 2.5f));
    }

    private boolean touch(View view, MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                if (closing) return true;
                removeCallbacks(expire);
                stopAnimation();
                clearTouch();
                downProgress = progress;
                dragDistance = Math.max(dp(24), capsule.getTop() + capsule.getHeight() / 2f - anchorY);
                downY = event.getRawY();
                downX = event.getRawX();
                velocity = VelocityTracker.obtain();
                addMovement(event);
                return true;
            case MotionEvent.ACTION_MOVE:
                if (velocity == null) return true;
                addMovement(event);
                float dy = event.getRawY() - downY;
                float dx = event.getRawX() - downX;
                if (!dragging && Math.abs(dx) > touchSlop && Math.abs(dx) > Math.abs(dy)) cancelled = true;
                if (!cancelled && (dragging || dy < -touchSlop)) {
                    dragging = true;
                    progress = dragProgress(downProgress, dy, dragDistance);
                    applyProgress();
                }
                return true;
            case MotionEvent.ACTION_UP:
                if (velocity == null) return true;
                addMovement(event);
                velocity.computeCurrentVelocity(1000);
                boolean launched = dragging && shouldDismiss(progress, velocity.getYVelocity());
                boolean click = !dragging && !cancelled && Math.abs(event.getRawY() - downY) <= touchSlop
                        && Math.abs(event.getRawX() - downX) <= touchSlop;
                clearTouch();
                if (launched) dismiss();
                else if (click) view.performClick();
                else animateTo(1f);
                return true;
            case MotionEvent.ACTION_POINTER_DOWN:
            case MotionEvent.ACTION_CANCEL:
                if (velocity != null) {
                    clearTouch();
                    animateTo(1f);
                }
                return true;
            default:
                return true;
        }
    }

    private static float dragProgress(float initialProgress, float dy, float travel) {
        return Math.max(0f, Math.min(1f, initialProgress + dy / travel));
    }

    private static boolean shouldDismiss(float progress, float velocityY) {
        return progress <= 0.58f || velocityY < -dp(650);
    }

    private void addMovement(MotionEvent event) {
        // Local event coordinates move with the animated view. Track raw screen motion.
        MotionEvent raw = MotionEvent.obtainNoHistory(event);
        raw.setLocation(event.getRawX(), event.getRawY());
        velocity.addMovement(raw);
        raw.recycle();
    }

    private void dismiss() {
        if (getVisibility() != VISIBLE || closing) return;
        closing = true;
        removeCallbacks(expire);
        clearTouch();
        animateTo(0f);
    }

    boolean isInteracting() {
        return velocity != null;
    }

    boolean isShowing() {
        return getVisibility() == VISIBLE && !closing;
    }

    void hide() {
        removeCallbacks(expire);
        stopAnimation();
        clearTouch();
        action = null;
        capsule.setContentDescription(null);
        title.setText(null);
        preview.setText(null);
        setVisibility(GONE);
    }

    private void clearTouch() {
        if (velocity != null) {
            velocity.recycle();
            velocity = null;
        }
        dragging = cancelled = false;
    }

    private void stopAnimation() {
        ValueAnimator previous = animator;
        animator = null;
        if (previous != null) previous.cancel();
    }
}
