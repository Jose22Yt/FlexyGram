package org.telegram.ui.Components;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.AndroidUtilities.dpf2;
import static org.telegram.messenger.AndroidUtilities.lerp;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.PorterDuff;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;

import androidx.annotation.DrawableRes;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.RawRes;

import org.telegram.messenger.LocaleController;
import org.telegram.messenger.utils.ViewOutlineProviderImpl;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProviderThemed;
import org.telegram.ui.Components.blur3.source.BlurredBackgroundSourceColor;

import java.util.ArrayList;

import me.vkryl.android.animator.BoolAnimator;
import me.vkryl.android.animator.FactorAnimator;

@SuppressLint("ViewConstructor")
public class FragmentFloatingButton extends FrameLayout implements FactorAnimator.Target {
    private final int ANIMATOR_ID_BUTTON_VISIBLE = 0;
    private final int ANIMATOR_ID_PROGRESS_VISIBLE = 1;

    private final BoolAnimator animatorButtonVisible = new BoolAnimator(ANIMATOR_ID_BUTTON_VISIBLE, this,
        CubicBezierInterpolator.EASE_OUT_QUINT, 380, true);

    private final BoolAnimator animatorProgressVisible = new BoolAnimator(ANIMATOR_ID_PROGRESS_VISIBLE, this,
        CubicBezierInterpolator.EASE_OUT_QUINT, 380);


    public final RLottieImageView imageView;
    public final RadialProgressView progressView;
    private final Theme.ResourcesProvider resourcesProvider;
    private ArrayList<View> additionalContentViews;
    private final boolean isSubButton;

    public FragmentFloatingButton(@NonNull Context context, Theme.ResourcesProvider resourcesProvider) {
        this(context, resourcesProvider, false);
    }

    public FragmentFloatingButton(@NonNull Context context, Theme.ResourcesProvider resourcesProvider, boolean isSubButton) {
        super(context);

        this.resourcesProvider = resourcesProvider;
        this.isSubButton = isSubButton;

        imageView = new RLottieImageView(context);
        imageView.setScaleType(ImageView.ScaleType.CENTER);
        addView(imageView, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT));

        progressView = new RadialProgressView(context);
        progressView.setSize(dp(18));
        progressView.setStrokeWidth(2);
        addView(progressView, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT));
        setAnimatedVisibility(progressView, 0);

        ScaleStateListAnimator.apply(this);
        if (!isSubButton) {
            // exteraGram 12.9.0, FragmentFloatingButton.java:67 — squircle вместо круга.
            setOutlineProvider(app.exteraless.appearance.AppearanceConfig.squareFab()
                    ? ViewOutlineProviderImpl.boundsWithPaddingRoundRect(0, dp(14))
                    : ViewOutlineProviderImpl.BOUNDS_OVAL);
            setTranslationZ(dpf2(0.5f));
        }

        if (isSubButton) {
            iBlur3ColorProviderTabs = new BlurredBackgroundColorProviderThemed(null, Theme.key_dialogBackground) {
                @Override
                public int getStrokeColorTop() {
                    return isDark() ? 0x06FFFFFF : 0x11000000;
                }

                @Override
                public int getStrokeColorBottom() {
                    return isDark() ? 0x11FFFFFF : 0x20000000;
                }

                @Override
                public int getShadowColor() {
                    return isDark() ? 0x04FFFFFF : 0x20000000;
                }
            };
            iBlur3SourceColor = new BlurredBackgroundSourceColor();
            iBlur3Background = iBlur3SourceColor.createDrawable();
            iBlur3Background.setColorProvider(iBlur3ColorProviderTabs);
            iBlur3Background.setStrokeWidth(dpf2(0.4f), dpf2(0.4f));
            iBlur3Background.setRadius(dp(app.exteraless.appearance.AppearanceConfig.squareFab() ? 10 : 18));
            iBlur3Background.setPadding(dp(5.66f));
        }

        updateColors();
    }

    public void setProgressVisible(boolean visible, boolean animated) {
        animatorProgressVisible.setValue(visible, animated);
    }

    public void setButtonVisible(boolean visible, boolean animated) {
        animatorButtonVisible.setValue(visible, animated);
    }

    public boolean getButtonVisible() {
        return animatorButtonVisible.getValue();
    }

    public boolean getProgressVisible() {
        return animatorProgressVisible.getValue();
    }

    @Override
    public void onFactorChanged(int id, float factor, float fraction, FactorAnimator callee) {
        if (id == ANIMATOR_ID_BUTTON_VISIBLE) {
            setAnimatedVisibility(this, factor);
            setClickable(factor >= 0.99f);
            setAdditionalTranslationY(dp(isSubButton ? 64 : 40) * (1f - factor));
        } else if (id == ANIMATOR_ID_PROGRESS_VISIBLE) {
            setAnimatedVisibility(progressView, factor);
            setAnimatedVisibility(imageView, 1f - factor);
            if (additionalContentViews != null) {
                for (View v : additionalContentViews) {
                    setAnimatedVisibility(v, 1f - factor);
                }
            }
        }
    }

    public void setAnimation(@RawRes int animation, int size) {
        imageView.setAnimation(animation, size, size);
    }

    public void setImageResource(@DrawableRes int drawable) {
        imageView.setImageResource(drawable);
    }

    private BlurredBackgroundSourceColor iBlur3SourceColor;
    private BlurredBackgroundDrawable iBlur3Background;
    private BlurredBackgroundColorProviderThemed iBlur3ColorProviderTabs;

    public void updateColors() {
        if (isSubButton) {
            imageView.setColorFilter(Theme.getColor(Theme.key_actionBarDefaultIcon, resourcesProvider), PorterDuff.Mode.SRC_IN);
            progressView.setProgressColor(Theme.getColor(Theme.key_actionBarDefaultIcon, resourcesProvider));

            iBlur3SourceColor.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
            iBlur3ColorProviderTabs.updateColors();
            iBlur3Background.updateColors();
            invalidate();

            int rad = dp(app.exteraless.appearance.AppearanceConfig.squareFab() ? 10 : 18);
            int pressedColor = Theme.getColor(Theme.key_listSelector, resourcesProvider);
            setBackground(Theme.createInsetRoundRectDrawable(pressedColor, rad, dp(6)));
        } else {
            imageView.setColorFilter(Theme.getColor(Theme.key_chats_actionIcon, resourcesProvider), PorterDuff.Mode.SRC_IN);
            progressView.setProgressColor(Theme.getColor(Theme.key_chats_actionIcon, resourcesProvider));
            setBackground(app.exteraless.utils.UIUtil.createFabSelectorDrawable(48,
                Theme.getColor(Theme.key_featuredStickers_addButton, resourcesProvider),
                Theme.getColor(Theme.key_featuredStickers_addButtonPressed, resourcesProvider)
            ));
        }
    }

    public static final int SIZE = 48;

    public static FrameLayout.LayoutParams createSubButtonLayoutParams() {
        return LayoutHelper.createFrame(48, 48,
                (LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT) | Gravity.BOTTOM,
                20, 0, 20, 14);
    }

    public static FrameLayout.LayoutParams createDefaultLayoutParams() {
        return LayoutHelper.createFrame(48, 48,
                (LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT) | Gravity.BOTTOM,
                20, 0, 20, 14);
    }


    public static FrameLayout.LayoutParams createDefaultLayoutParamsBig() {
        return LayoutHelper.createFrame(56, 56,
                (LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT) | Gravity.BOTTOM,
                20 /*24*/, 0, 20 /*24*/, 14 /*16*/);
    }

    private float additionalTranslationY;
    private float internalTranslationY;
    private boolean setTranslationInternal;

    private void setAdditionalTranslationY(float translationY) {
        if (additionalTranslationY != translationY) {
            setTranslationInternal = true;
            super.setTranslationY(internalTranslationY + translationY);
            setTranslationInternal = false;
            additionalTranslationY = translationY;
        }
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        if (iBlur3Background != null) {
            iBlur3Background.setBounds(0, 0, w, h);
        }
    }

    private app.flexygram.effects.ChatEdgeReflection colorOsEdge;
    private boolean colorOsAppliedOnBlur;

    @Override
    public void draw(@NonNull Canvas canvas) {
        if (iBlur3Background != null) {
            final boolean colorOs = app.flexygram.effects.ChatEdgeStyle.isColorOsGlass();
            if (colorOs) {
                final boolean dark = resourcesProvider != null ? resourcesProvider.isDark() : Theme.isCurrentThemeDark();
                colorOsEdge = app.flexygram.effects.ChatEdgeStyle.updateReflection(colorOsEdge);
                colorOsAppliedOnBlur = true;
                iBlur3Background.drawWithChatEdge(canvas, colorOsEdge, dark);
            } else if (colorOsAppliedOnBlur) {
                colorOsAppliedOnBlur = false;
                iBlur3Background.drawWithChatEdge(canvas, null, false);
            } else {
                iBlur3Background.draw(canvas);
            }
        }
        super.draw(canvas);
    }

    @Override
    protected void dispatchDraw(@NonNull Canvas canvas) {
        if (iBlur3Background == null && app.flexygram.effects.ChatEdgeStyle.isColorOsGlass()) {
            final int w = getWidth();
            final int h = getHeight();
            if (w > 0 && h > 0) {
                final float l = getPaddingLeft();
                final float t = getPaddingTop();
                final float rBound = w - getPaddingRight();
                final float bBound = h - getPaddingBottom();
                final float bw = rBound - l;
                final float bh = bBound - t;
                if (bw > 0 && bh > 0) {
                    final boolean dark = resourcesProvider != null ? resourcesProvider.isDark() : Theme.isCurrentThemeDark();
                    colorOsEdge = app.flexygram.effects.ChatEdgeStyle.updateReflection(colorOsEdge);
                    final int sizeDp = Math.max(1, Math.round(Math.min(bw, bh) / Math.max(1f, org.telegram.messenger.AndroidUtilities.density)));
                    final float r = Math.min(Math.min(bw, bh) * 0.5f,
                            dp(app.exteraless.appearance.AppearanceConfig.fabCornerRadius(sizeDp)));
                    colorOsEdge.draw(canvas, l, t, rBound, bBound, r, dark, 255);
                }
            }
        }
        super.dispatchDraw(canvas);
    }

    @Override
    public void setTranslationY(float translationY) {
        if (internalTranslationY != translationY) {
            setTranslationInternal = true;
            super.setTranslationY(translationY + additionalTranslationY);
            setTranslationInternal = false;
            internalTranslationY = translationY;
        }
    }

    @Override
    public float getTranslationY() {
        if (setTranslationInternal) {
            return super.getTranslationY();
        }

        return internalTranslationY;
    }

    public void addAdditionalView(View view) {
        if (additionalContentViews == null) {
            additionalContentViews = new ArrayList<>();
        }
        additionalContentViews.add(view);
        setAnimatedVisibility(view, 1f - animatorProgressVisible.getFloatValue());
    }

    public static void setAnimatedVisibility(@Nullable View v, float f) {
        if (v == null) {
            return;
        }

        v.setAlpha(f);
        v.setScaleX(lerp(0.4f, 1f, f));
        v.setScaleY(lerp(0.4f, 1f, f));
        v.setVisibility(f > 0 ? VISIBLE : GONE);
    }
}
