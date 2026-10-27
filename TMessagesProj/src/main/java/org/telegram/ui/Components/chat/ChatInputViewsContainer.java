package org.telegram.ui.Components.chat;

import static org.telegram.messenger.AndroidUtilities.dp;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.os.Build;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.RoundedCorner;
import android.view.View;
import android.view.WindowInsets;
import android.widget.FrameLayout;

import androidx.annotation.NonNull;

import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.ChatActivityEnterView;
import org.telegram.ui.ActionBar.Theme;
import androidx.core.graphics.ColorUtils;
import org.telegram.messenger.AndroidUtilities;
import app.flexygram.composer.FlexyComposerConfig;
import org.telegram.ui.Components.blur3.BlurredBackgroundWithFadeDrawable;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.inset.InAppKeyboardInsetView;
import org.telegram.ui.Components.inset.WindowInsetsProvider;

public class ChatInputViewsContainer extends FrameLayout {
    public static final int INPUT_BUBBLE_RADIUS = 22;
    public static final int INPUT_KEYBOARD_RADIUS = 29;

    public static final int INPUT_BUBBLE_BOTTOM = 9;

    private WindowInsetsProvider windowInsetsProvider;

    private final View fadeView;
    private final FrameLayout inputIslandBubbleContainer;
    private final FrameLayout inAppKeyboardBubbleContainer;
    private ChatActivityEnterView flexyComposer;
    private org.telegram.ui.Components.chat.layouts.ChatActivityChannelButtonsLayout flexyChannels;
    private int flexyNativeLeftMargin, flexyNativeRightMargin;
    private boolean flexyPearlGlass;
    private final SharedPreferences.OnSharedPreferenceChangeListener flexyListener = (prefs, key) -> {
        flexyPearlGlass = FlexyComposerConfig.glass();
        // Surface changes never request layout or change insets.
        invalidate();
    };

    public ChatInputViewsContainer(@NonNull Context context) {
        super(context);

        inputIslandBubbleContainer = new FrameLayout(context) {
            @Override protected void onMeasure(int widthSpec, int heightSpec) {
                if (flexyComposer != null) {
                    LayoutParams lp = (LayoutParams) flexyComposer.getLayoutParams();
                    int width = MeasureSpec.getSize(widthSpec);
                    lp.leftMargin = flexyComposer.getFlexyHorizontalMargin(width, flexyNativeLeftMargin);
                    lp.rightMargin = flexyComposer.getFlexyHorizontalMargin(width, flexyNativeRightMargin);
                }
                super.onMeasure(widthSpec, heightSpec);
            }
            @Override public void onViewAdded(View child) {
                super.onViewAdded(child);
                if(child instanceof org.telegram.ui.Components.chat.layouts.ChatActivityChannelButtonsLayout){
                    flexyChannels=(org.telegram.ui.Components.chat.layouts.ChatActivityChannelButtonsLayout)child;
                    flexyChannels.setSignaturePresentation(true);
                }
                if (child instanceof ChatActivityEnterView) {
                    flexyComposer = (ChatActivityEnterView) child;
                    LayoutParams lp = (LayoutParams) child.getLayoutParams();
                    flexyNativeLeftMargin = lp.leftMargin;
                    flexyNativeRightMargin = lp.rightMargin;
                }
            }
            @Override public void onViewRemoved(View child) {
                super.onViewRemoved(child);
                if (child == flexyComposer) flexyComposer = null;
                if (child == flexyChannels) flexyChannels = null;
            }
        };
        addView(inputIslandBubbleContainer,
            LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, Gravity.BOTTOM));

        inAppKeyboardBubbleContainer = new FrameLayout(context) {
            @Override
            public void addView(View child, int width, int height) {
                super.addView(child, width, height);
                checkViewsPositions();
            }
        };
        addView(inAppKeyboardBubbleContainer,
            LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, Gravity.BOTTOM));

        fadeView = new View(context) {
            @Override
            protected void dispatchDraw(@NonNull Canvas canvas) {
                if (backgroundWithFadeDrawable != null) {
                    backgroundWithFadeDrawable.draw(canvas);
                }
                super.dispatchDraw(canvas);
            }
        };
    }

    public View getFadeView() {
        return fadeView;
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        flexyPearlGlass = FlexyComposerConfig.glass();
        FlexyComposerConfig.preferences().registerOnSharedPreferenceChangeListener(flexyListener);
    }

    @Override protected void onDetachedFromWindow() {
        FlexyComposerConfig.preferences().unregisterOnSharedPreferenceChangeListener(flexyListener);
        super.onDetachedFromWindow();
    }

    public void setWindowInsetsProvider(WindowInsetsProvider windowInsetsProvider) {
        this.windowInsetsProvider = windowInsetsProvider;
    }



    public boolean drawInputBackground = true;
    public BlurredBackgroundDrawable blurredBackgroundDrawable;
    private BlurredBackgroundDrawable underKeyboardBackgroundDrawable;
    public void setInputIslandBubbleDrawable(BlurredBackgroundDrawable drawable) {
        blurredBackgroundDrawable = drawable;
        blurredBackgroundDrawable.setPadding(dp(7));
        blurredBackgroundDrawable.setRadius(dp(INPUT_BUBBLE_RADIUS));
    }

    public void setUnderKeyboardBackgroundDrawable(BlurredBackgroundDrawable drawable) {
        underKeyboardBackgroundDrawable = drawable;
        underKeyboardBackgroundDrawable.enableInAppKeyboardOptimization();
        underKeyboardBackgroundDrawable.setRadius(dp(INPUT_KEYBOARD_RADIUS), dp(INPUT_KEYBOARD_RADIUS), 0, 0);
        underKeyboardBackgroundDrawable.setThickness(dp(32));
        underKeyboardBackgroundDrawable.setIntensity(0.4f);
    }

    public void updateColors() {
        blurredBackgroundDrawable.updateColors();
        underKeyboardBackgroundDrawable.updateColors();
        invalidate();
    }


    @NonNull
    public FrameLayout getInputIslandBubbleContainer() {
        return inputIslandBubbleContainer;
    }

    @NonNull
    public FrameLayout getInAppKeyboardBubbleContainer() {
        return inAppKeyboardBubbleContainer;
    }

    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        super.onLayout(changed, left, top, right, bottom);
        checkViewsPositions();
        checkInAppKeyboardChild();
    }



    private void checkInAppKeyboardViewHeight() {
        LayoutParams lp = (LayoutParams) inAppKeyboardBubbleContainer.getLayoutParams();

        final int oldHeight = lp.height;
        final int newHeight = windowInsetsProvider.getInAppKeyboardRecommendedViewHeight();

        if (oldHeight != newHeight) {
            lp.height = newHeight;
            requestLayout();
        }
    }

    private final Path underKeyboardPath = new Path();

    private int currentBlurredHeight;
    private void checkBlurredHeight(boolean force) {
        checkViewsPositions();

        final int blurredHeight = inputBubbleHeightRound + dp(INPUT_BUBBLE_BOTTOM) + Math.round(maxBottomInset);
        if (currentBlurredHeight != blurredHeight || force) {
            currentBlurredHeight = blurredHeight;

            final int r = dp(INPUT_KEYBOARD_RADIUS);
            tmpRectF.set(0, getMeasuredHeight() - imeBottomInset, getMeasuredWidth(), getMeasuredHeight());
            underKeyboardPath.rewind();
            underKeyboardPath.addRoundRect(tmpRectF, new float[] {r, r, r, r, 0, 0, 0, 0}, Path.Direction.CW);
            underKeyboardPath.close();
            invalidate();
        }
    }

    private float maxBottomInset;
    private float imeBottomInset;
    private boolean needDrawInAppKeyboard;

    public void checkInsets() {
        maxBottomInset = windowInsetsProvider.getAnimatedMaxBottomInset();
        imeBottomInset = windowInsetsProvider.getAnimatedImeBottomInset();

        needDrawInAppKeyboard = windowInsetsProvider.inAppViewIsVisible();

        if ((inAppKeyboardBubbleContainer.getVisibility() == VISIBLE) != needDrawInAppKeyboard) {
            inAppKeyboardBubbleContainer.setVisibility(needDrawInAppKeyboard ? VISIBLE : GONE);
        }

        checkInAppKeyboardViewHeight();
        checkBlurredHeight(false);
        checkInAppKeyboardChild();

        if (underKeyboardBackgroundDrawable != null) {
            int leftBottomRadius = 0;
            int rightBottomRadius = 0;
            if (Build.VERSION.SDK_INT >= 31) {
                final WindowInsets insets = getRootWindowInsets();
                if (insets != null) {
                    final RoundedCorner bottomLeft = insets.getRoundedCorner(RoundedCorner.POSITION_BOTTOM_LEFT);
                    final RoundedCorner bottomRight = insets.getRoundedCorner(RoundedCorner.POSITION_BOTTOM_RIGHT);
                    leftBottomRadius = bottomLeft == null ? 0 : bottomLeft.getRadius();
                    rightBottomRadius = bottomRight == null ? 0 : bottomRight.getRadius();
                }
            }
            underKeyboardBackgroundDrawable.setRadius(dp(INPUT_KEYBOARD_RADIUS), dp(INPUT_KEYBOARD_RADIUS), rightBottomRadius, leftBottomRadius, true);
        }
    }

    private void checkViewsPositions() {
        inputIslandBubbleContainer.setTranslationY(-maxBottomInset - dp(INPUT_BUBBLE_BOTTOM)
            - (flexyChannels!=null&&flexyChannels.isSignatureCompactPresentation()?flexyChannels.getSignatureVerticalOffset()*flexyChannels.getSignatureAlpha():
                (flexyComposer == null ? 0 : flexyComposer.getFlexyVerticalOffset())));
        inAppKeyboardBubbleContainer.setTranslationY(inAppKeyboardBubbleContainer.getMeasuredHeight() - imeBottomInset);
    }


    private void checkInAppKeyboardChild() {
        final int navbarHeight = windowInsetsProvider.getCurrentNavigationBarInset();
        final float keyboardHeight = windowInsetsProvider.getAnimatedImeBottomInset();

        for (int a = 0, N = inAppKeyboardBubbleContainer.getChildCount(); a < N; a++) {
            final View child = inAppKeyboardBubbleContainer.getChildAt(a);
            if (child instanceof InAppKeyboardInsetView) {
                InAppKeyboardInsetView insetView = (InAppKeyboardInsetView) child;
                insetView.applyNavigationBarHeight(navbarHeight);
                insetView.applyInAppKeyboardAnimatedHeight(keyboardHeight);
            }
        }
    }



    /* */

    private float inputBubbleOffsetLeft;
    private float inputBubbleOffsetRight;

    private float inputBubbleHeight;
    private int inputBubbleHeightRound;
    public void setInputBubbleHeight(float height) {
        inputBubbleHeight = height;
        inputBubbleHeightRound = Math.round(inputBubbleHeight);
        checkBlurredHeight(false);
    }

    public void setInputBubbleOffsets(float left, float right) {
        inputBubbleOffsetLeft = left;
        inputBubbleOffsetRight = right;
        invalidate();
    }

    public float getInputBubbleHeight() {
        return inputBubbleHeight;
    }

    public float getInputBubbleTop() {
        return getInputBubbleBottom() - getInputBubbleHeight();
    }

    public float getInputBubbleBottom() {
        return getMeasuredHeight() - maxBottomInset - dp(INPUT_BUBBLE_BOTTOM);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
        checkBlurredHeight(true);
        checkDrawableBounds();
        checkViewsPositions();
        checkInAppKeyboardChild();
    }

    /* Render */

    private final Rect tmpRect = new Rect();
    private final RectF tmpRectF = new RectF();

    @Override
    protected void dispatchDraw(@NonNull Canvas canvas) {
        underKeyboardBackgroundDrawable.setBounds(
            0,
            getMeasuredHeight() - (int) imeBottomInset,
            getMeasuredWidth(),
            Math.max(getMeasuredHeight(), getMeasuredHeight() - (int) imeBottomInset + dp(INPUT_KEYBOARD_RADIUS * 2))
        );

        flexyVoiceDrawn = false;
        final int blurTop = getMeasuredHeight() - currentBlurredHeight;

        tmpRect.set(
            Math.round(inputBubbleOffsetLeft),
            0,
            getMeasuredWidth() - Math.round(inputBubbleOffsetRight),
            inputBubbleHeightRound
        );
        tmpRect.inset(0, -dp(7));
        tmpRect.offset(0, blurTop + (int) bubbleInputTranlationY);

        blurredBackgroundDrawable.setBounds(tmpRect);
        if (drawInputBackground) {
            if (flexyComposer != null && flexyComposer.isFlexyCompactPresentation()) {
                drawFlexyCompactBackground(canvas);
            } else if(flexyChannels!=null&&flexyChannels.isSignatureCompactPresentation()){
                drawSignatureChannelBackground(canvas);
            } else {
                blurredBackgroundDrawable.draw(canvas);
            }
        }

        if (flexyComposer != null) flexyComposer.setFlexyVoiceBackdropDrawn(flexyVoiceDrawn);
        if (needDrawInAppKeyboard) {
            underKeyboardBackgroundDrawable.draw(canvas);
        }

        super.dispatchDraw(canvas);
    }

    private final RectF signatureChannelMiddle=new RectF(),signatureChannelLeft=new RectF(),signatureChannelRight=new RectF();
    private final RectF signatureChannelLastMiddle=new RectF(),signatureChannelLastLeft=new RectF(),signatureChannelLastRight=new RectF();
    private final Path signatureChannelMask=new Path();
    /** Same native backdrop as the ordinary composer; one pass clipped to three independent pieces. */
    private void drawSignatureChannelBackground(Canvas canvas){
        flexyChannels.getSignatureBounds(signatureChannelMiddle,signatureChannelLeft,signatureChannelRight);
        float x=inputIslandBubbleContainer.getX()+flexyChannels.getX();
        float y=inputIslandBubbleContainer.getY()+flexyChannels.getY();
        signatureChannelMiddle.offset(x,y);
        if(!signatureChannelLeft.isEmpty())signatureChannelLeft.offset(x,y);
        if(!signatureChannelRight.isEmpty())signatureChannelRight.offset(x,y);
        float radius=(dp(44)-2*flexyChannels.getSignatureVisualInset())/2f;
        if(!signatureChannelMiddle.equals(signatureChannelLastMiddle)||!signatureChannelLeft.equals(signatureChannelLastLeft)||!signatureChannelRight.equals(signatureChannelLastRight)){
            signatureChannelMask.rewind();signatureChannelMask.addRoundRect(signatureChannelMiddle,radius,radius,Path.Direction.CW);
            if(!signatureChannelLeft.isEmpty())signatureChannelMask.addRoundRect(signatureChannelLeft,radius,radius,Path.Direction.CW);
            if(!signatureChannelRight.isEmpty())signatureChannelMask.addRoundRect(signatureChannelRight,radius,radius,Path.Direction.CW);
            signatureChannelLastMiddle.set(signatureChannelMiddle);signatureChannelLastLeft.set(signatureChannelLeft);signatureChannelLastRight.set(signatureChannelRight);
        }
        int panel=flexyChannels.getSignatureSurfaceColor();boolean dark=ColorUtils.calculateLuminance(panel)<.4;
        if(flexyPearlGlass){
            tmpRectF.set(signatureChannelMiddle);if(!signatureChannelLeft.isEmpty())tmpRectF.union(signatureChannelLeft);if(!signatureChannelRight.isEmpty())tmpRectF.union(signatureChannelRight);
            tmpRectF.inset(-dp(7),-dp(7));tmpRectF.round(tmpRect);blurredBackgroundDrawable.setBounds(tmpRect);
            canvas.save();canvas.clipPath(signatureChannelMask);blurredBackgroundDrawable.draw(canvas);canvas.restore();
            flexySurface.setColor(ColorUtils.setAlphaComponent(app.flexygram.composer.ComposerStyle.surface(dark,false),(dark?80:60)*blurredBackgroundDrawable.getAlpha()/255));
        }else flexySurface.setColor(app.flexygram.composer.ComposerStyle.surface(dark,false));
        flexySurface.setAlpha(Math.round(flexySurface.getAlpha()*flexyChannels.getSignatureAlpha()));
        canvas.drawRoundRect(signatureChannelMiddle,radius,radius,flexySurface);
        if(!signatureChannelLeft.isEmpty())canvas.drawRoundRect(signatureChannelLeft,radius,radius,flexySurface);
        if(!signatureChannelRight.isEmpty())canvas.drawRoundRect(signatureChannelRight,radius,radius,flexySurface);
        if(flexyPearlGlass){
            flexyPearl.setColor(ColorUtils.setAlphaComponent(Color.WHITE,(dark?28:76)*blurredBackgroundDrawable.getAlpha()/255));
            flexyPearl.setStyle(Paint.Style.STROKE);flexyPearl.setStrokeWidth(.65f*AndroidUtilities.density);
            canvas.drawRoundRect(signatureChannelMiddle,radius,radius,flexyPearl);
            if(!signatureChannelLeft.isEmpty())canvas.drawRoundRect(signatureChannelLeft,radius,radius,flexyPearl);
            if(!signatureChannelRight.isEmpty())canvas.drawRoundRect(signatureChannelRight,radius,radius,flexyPearl);
        }
    }

    private final RectF flexyPill = new RectF();
    private final RectF flexyAttach = new RectF();
    private final RectF flexyVoice = new RectF();
    private final RectF flexyLastVoice = new RectF();
    private boolean flexyLastHasVoice;
    private boolean flexyVoiceDrawn;
    private final Path flexyMask = new Path();
    private final RectF flexyLastPill = new RectF();
    private final RectF flexyLastAttach = new RectF();
    private boolean flexyLastHasAttach;
    private final Paint flexySurface = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint flexyPearl = new Paint(Paint.ANTI_ALIAS_FLAG);

    private void drawFlexyCompactBackground(Canvas canvas) {
        if (!flexyComposer.getFlexyTextPillBounds(flexyPill)) return;
        final float offsetX = inputIslandBubbleContainer.getX() + flexyComposer.getX();
        final float offsetY = inputIslandBubbleContainer.getY() + flexyComposer.getY();
        flexyPill.offset(offsetX, offsetY);
        final boolean attach = flexyComposer.getFlexyAttachmentBounds(flexyAttach);
        if (attach) flexyAttach.offset(offsetX, offsetY);
        final float radius = (dp(44) - 2 * flexyComposer.getFlexyVisualInset()) / 2f;
        if (flexyPearlGlass) {
            final boolean voice = flexyComposer.getFlexyVoiceBounds(flexyVoice);
            if (voice) flexyVoice.offset(offsetX, offsetY);
            // One native backdrop pass for the pill, attachment and settled microphone.
            // No second blur engine, drawable factory or animation controller.
            if (!flexyPill.equals(flexyLastPill) || attach != flexyLastHasAttach || attach && !flexyAttach.equals(flexyLastAttach)
                    || voice != flexyLastHasVoice || voice && !flexyVoice.equals(flexyLastVoice)) {
                flexyMask.rewind();
                flexyMask.addRoundRect(flexyPill, radius, radius, Path.Direction.CW);
                if (attach) flexyMask.addRoundRect(flexyAttach, radius, radius, Path.Direction.CW);
                if (voice) flexyMask.addRoundRect(flexyVoice, radius, radius, Path.Direction.CW);
                flexyLastVoice.set(flexyVoice);
                flexyLastHasVoice = voice;
                flexyLastPill.set(flexyPill);
                flexyLastAttach.set(flexyAttach);
                flexyLastHasAttach = attach;
            }
            canvas.save();
            canvas.clipPath(flexyMask);
            blurredBackgroundDrawable.draw(canvas);
            canvas.restore();
            final int color = flexyComposer.getThemedColor(Theme.key_chat_messagePanelBackground);
            final boolean dark = ColorUtils.calculateLuminance(color) < 0.4;
            // A cheap tonal wash preserves the native backdrop and chat legibility.
            flexySurface.setColor(ColorUtils.setAlphaComponent(
                app.flexygram.composer.ComposerStyle.surface(dark, false),
                (dark ? 80 : 60) * blurredBackgroundDrawable.getAlpha() / 255));
            canvas.drawRoundRect(flexyPill, radius, radius, flexySurface);
            if (attach) canvas.drawRoundRect(flexyAttach, radius, radius, flexySurface);
            if (voice) canvas.drawRoundRect(flexyVoice, radius, radius, flexySurface);
            flexyPearl.setColor(ColorUtils.setAlphaComponent(Color.WHITE,
                (dark ? 28 : 76) * blurredBackgroundDrawable.getAlpha() / 255));
            flexyPearl.setStyle(Paint.Style.STROKE);
            flexyPearl.setStrokeWidth(0.65f * AndroidUtilities.density);
            canvas.drawRoundRect(flexyPill, radius, radius, flexyPearl);
            if (attach) canvas.drawRoundRect(flexyAttach, radius, radius, flexyPearl);
            if (voice) canvas.drawRoundRect(flexyVoice, radius, radius, flexyPearl);
            flexyVoiceDrawn = voice;
        } else {
            // Opaque, legible off-white/charcoal surfaces without a full-width backing.
            final int panel = flexyComposer.getThemedColor(Theme.key_chat_messagePanelBackground);
            flexySurface.setColor(app.flexygram.composer.ComposerStyle.surface(ColorUtils.calculateLuminance(panel) < 0.4, false));
            canvas.drawRoundRect(flexyPill, radius, radius, flexySurface);
            if (attach) canvas.drawRoundRect(flexyAttach, radius, radius, flexySurface);
        }
    }

    @Override
    protected boolean drawChild(@NonNull Canvas canvas, View child, long drawingTime) {
        final boolean needClip = child == inAppKeyboardBubbleContainer;
        if (needClip) {
            canvas.save();
            canvas.clipPath(underKeyboardBackgroundDrawable.getPath());
        }

        final boolean result = super.drawChild(canvas, child, drawingTime);
        if (needClip) {
            canvas.restore();
        }

        return result;
    }





    private BlurredBackgroundWithFadeDrawable backgroundWithFadeDrawable;

    public void setBackgroundWithFadeDrawable(BlurredBackgroundWithFadeDrawable backgroundWithFadeDrawable) {
        this.backgroundWithFadeDrawable = backgroundWithFadeDrawable;
    }

    private float blurredBottomHeight;
    public void setBlurredBottomHeight(float height) {
        if (blurredBottomHeight != height) {
            blurredBottomHeight = height;
            checkDrawableBounds();
        }
    }

    private float bubbleInputTranlationY;
    public void setInputBubbleTranslationY(float translationY) {
        this.bubbleInputTranlationY = translationY;
        invalidate();
    }

    public void setInputBubbleAlpha(int alpha) {
        if (blurredBackgroundDrawable != null) {
            blurredBackgroundDrawable.setAlpha(alpha);
        }

    }

    private void checkDrawableBounds() {
        if (backgroundWithFadeDrawable == null) {
            return;
        }

        final int oldBound = backgroundWithFadeDrawable.getBounds().top;
        final int newBound = getMeasuredHeight() - Math.round(blurredBottomHeight);

        if (oldBound != newBound) {
            backgroundWithFadeDrawable.setBounds(0, newBound, getMeasuredWidth(), getMeasuredHeight());
            fadeView.invalidate(0, Math.max(0, Math.min(oldBound, newBound)), getMeasuredWidth(), getMeasuredHeight());
            invalidate(0, Math.max(0, Math.min(oldBound, newBound)), getMeasuredWidth(), getMeasuredHeight());
        }
    }


    private boolean captured;

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        final int action = event.getAction();

        if (action == MotionEvent.ACTION_DOWN) {
            final int x = (int) event.getX();
            final int y = (int) event.getY();

            captured = blurredBackgroundDrawable != null && blurredBackgroundDrawable.getAlpha() == 255 && blurredBackgroundDrawable.getBounds().contains(x, y)
                || underKeyboardBackgroundDrawable != null && underKeyboardBackgroundDrawable.getBounds().contains(x, y);

        }
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            captured = false;
        }

        return captured;
    }
}
