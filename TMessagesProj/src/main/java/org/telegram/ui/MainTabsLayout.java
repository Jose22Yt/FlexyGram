package org.telegram.ui;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.AndroidUtilities.lerp;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewConfiguration;
import app.flexygram.navigation.LiquidNavigationConfig;
import app.flexygram.navigation.LiquidNavigationMath;
import app.flexygram.navigation.LiquidLensRenderer;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.dynamicanimation.animation.DynamicAnimation;
import androidx.dynamicanimation.animation.FloatPropertyCompat;
import androidx.dynamicanimation.animation.SpringAnimation;
import androidx.dynamicanimation.animation.SpringForce;

import android.util.Log;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.AnimatedLinearLayout;
import org.telegram.ui.Components.CubicBezierInterpolator;
import org.telegram.ui.Components.glass.GlassTabView;

import app.exteraless.appearance.MainTabsUiHelper;

import java.util.HashSet;
import java.util.Set;

import me.vkryl.android.animator.BoolAnimator;
import me.vkryl.android.animator.ListAnimator;
import me.vkryl.android.util.ClickHelper;

import tw.nekomimi.nekogram.NekoConfig;
import xyz.nextalone.nagram.NaConfig;

@SuppressLint("ViewConstructor")
public class MainTabsLayout extends AnimatedLinearLayout {

    public static final int BOTTOM_NAVIGATION_MODE_SHOW = 0;
    public static final int BOTTOM_NAVIGATION_MODE_HIDE = 1;
    public static final int BOTTOM_NAVIGATION_MODE_FLOATING = 2;

    private static final String KEY_BOTTOM_NAVIGATION_FLOATING = "OEAppearanceBottomNavigationFloating";

    private static Boolean bottomNavigationFloating;

    public static int getBottomNavigationMode() {
        if (isBottomNavigationHidden()) {
            return BOTTOM_NAVIGATION_MODE_HIDE;
        }
        return isBottomNavigationFloating() ? BOTTOM_NAVIGATION_MODE_FLOATING : BOTTOM_NAVIGATION_MODE_SHOW;
    }

    public static void setBottomNavigationMode(int mode) {
        NaConfig.INSTANCE.getHideBottomNavigationBar().setConfigBool(mode == BOTTOM_NAVIGATION_MODE_HIDE);
        final boolean floating = mode == BOTTOM_NAVIGATION_MODE_FLOATING;
        bottomNavigationFloating = floating;
        final SharedPreferences preferences = getBottomNavigationPreferences();
        if (preferences != null) {
            preferences.edit().putBoolean(KEY_BOTTOM_NAVIGATION_FLOATING, floating).apply();
        }
    }

    public static boolean isBottomNavigationHidden() {
        return NaConfig.INSTANCE.getHideBottomNavigationBar().Bool();
    }

    public static boolean isBottomNavigationVisible() {
        return !isBottomNavigationHidden();
    }

    public static boolean isBottomNavigationFloating() {
        if (isBottomNavigationHidden()) {
            return false;
        }
        if (bottomNavigationFloating == null) {
            final SharedPreferences preferences = getBottomNavigationPreferences();
            if (preferences == null) {
                return false;
            }
            bottomNavigationFloating = preferences.getBoolean(KEY_BOTTOM_NAVIGATION_FLOATING, false);
        }
        return bottomNavigationFloating;
    }

    private static SharedPreferences getBottomNavigationPreferences() {
        return ApplicationLoader.applicationContext == null ? null : NekoConfig.getPreferences();
    }

    private final Theme.ResourcesProvider resourcesProvider;

    public MainTabsLayout(Context context, Theme.ResourcesProvider resourcesProvider) {
        super(context);
        this.resourcesProvider = resourcesProvider;
        setClipToPadding(false);
    }

    private static final float[] PASS_TEXT_SIZES_DP = {12f, 12f, 10f};
    private static final int[] PASS_PADDINGS_DP = {16, 8, 4};

    private int maxWidthPx;

    public void setMaxWidth(int maxWidthPx) {
        if (this.maxWidthPx != maxWidthPx) {
            this.maxWidthPx = maxWidthPx;
            requestLayout();
        }
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int width = MeasureSpec.getSize(widthMeasureSpec);
        final int height = MeasureSpec.getSize(heightMeasureSpec);
        final int tabHeight = height - getPaddingTop() - getPaddingBottom();

        if (maxWidthPx > 0 && width > maxWidthPx) {
            width = maxWidthPx;
        }

        final boolean customSizing = LiquidNavigationConfig.configured();
        if (customSizing) {
            int count=0;for(int i=0;i<getChildCount();i++)if(isViewVisible(getChildAt(i)))count++;
            int slot=dp(LiquidNavigationConfig.slotDp(count,(int)(width/getResources().getDisplayMetrics().density)));
            int userWidth=width*(70+LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.WIDTH)*30/100)/100;
            width=Math.min(width,Math.max(dp(48)*Math.min(2,count)+getPaddingLeft()+getPaddingRight(),userWidth));
            measureTabTexts(LiquidNavigationConfig.compaction()==2?10:11);
            applyPassTextSize(LiquidNavigationConfig.compaction()==2?2:1);
            int inner=Math.max(1,width-getPaddingLeft()-getPaddingRight());
            int each=count*slot<=inner?inner/Math.max(1,count):slot;
            int total=0;
            for(int i=0;i<getChildCount();i++){
                View child=getChildAt(i);tabsWidth[i]=isViewVisible(child)?each:0;
                tabsLeftPos[i]=total;total+=tabsWidth[i];
                child.measure(MeasureSpec.makeMeasureSpec(tabsWidth[i],MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(tabHeight,MeasureSpec.EXACTLY));
            }
            flexyContentWidth=total+getPaddingLeft()+getPaddingRight();
            setMeasuredDimension(width,height);calculateTotalSizesAfterMeasure();return;
        }
        final boolean fillWidth = customSizing || MainTabsUiHelper.isMaterial3NavigationBar() || MainTabsUiHelper.isIosNavigationBar();
        final int maxTotalWidthForTabs = width - getPaddingLeft() - getPaddingRight();
        final int minTotalWidthForTabs = fillWidth
                ? maxTotalWidthForTabs
                : Math.min(dp(320), maxTotalWidthForTabs);

        int chosenPass = PASS_TEXT_SIZES_DP.length - 1;
        float lastMeasuredTextSize = -1;
        for (int pass = 0; pass < PASS_TEXT_SIZES_DP.length; pass++) {
            if (PASS_TEXT_SIZES_DP[pass] != lastMeasuredTextSize) {
                measureTabTexts(PASS_TEXT_SIZES_DP[pass]);
                lastMeasuredTextSize = PASS_TEXT_SIZES_DP[pass];
            }
            final int padding = dp(PASS_PADDINGS_DP[pass]);
            float total = 0;
            for (int a = 0, N = getChildCount(); a < N; a++) {
                if (!isViewVisible(getChildAt(a))) continue;
                final float withMargin = tabsTextWidth[a] + padding * 2;
                total += withMargin;
            }
            final boolean fits = total <= maxTotalWidthForTabs;
            if (fits || pass == PASS_TEXT_SIZES_DP.length - 1) {
                chosenPass = pass;
                break;
            }
        }

        applyPassTextSize(chosenPass);

        final int tabPadding = dp(customSizing ? LiquidNavigationConfig.spacingDp() : PASS_PADDINGS_DP[chosenPass]);
        final int maxTabTextWidthIfEq = (maxTotalWidthForTabs / Math.max(1, visibleChildCount)) - tabPadding * 2;

        float totalWidth = 0;
        int totalWeight = 0;
        for (int a = 0, N = getChildCount(); a < N; a++) {
            final View child = getChildAt(a);
            if (!isViewVisible(child)) {
                tabsTextWidth[a] = tabsTextWidthWithMargin[a] = 0;
                tabsWeight[a] = 0;
                continue;
            }

            tabsTextWidthWithMargin[a] = tabsTextWidth[a] + tabPadding * 2;
            tabsWeight[a] = tabsTextWidthWithMargin[a] > (maxTabTextWidthIfEq + tabPadding * 2) ? 0 : 1;

            totalWidth += tabsTextWidthWithMargin[a];
            totalWeight += tabsWeight[a];
        }

        if (totalWeight == 0) {
            for (int a = 0, N = getChildCount(); a < N; a++) {
                tabsWeight[a] = isViewVisible(getChildAt(a)) ? 1 : 0;
            }
            totalWeight = visibleChildCount;
        }

        if (totalWidth > maxTotalWidthForTabs) {
            final float m = maxTotalWidthForTabs / totalWidth;
            for (int a = 0, N = getChildCount(); a < N; a++) {
                tabsTextWidthWithMargin[a] *= m;
            }
        } else if (totalWidth < minTotalWidthForTabs) {
            final float growW = minTotalWidthForTabs - totalWidth;
            final float growP = growW / totalWeight;

            for (int a = 0, N = getChildCount(); a < N; a++) {
                tabsTextWidthWithMargin[a] += growP * tabsWeight[a];
            }
        }

        if (MainTabsUiHelper.isMaterial3NavigationBar() && visibleChildCount > 0) {
            final float share = (float) maxTotalWidthForTabs / visibleChildCount;
            boolean fitsEqually = true;
            for (int a = 0, N = getChildCount(); a < N; a++) {
                if (isViewVisible(getChildAt(a)) && tabsTextWidth[a] + tabPadding * 2 > share) {
                    fitsEqually = false;
                    break;
                }
            }
            if (fitsEqually) {
                for (int a = 0, N = getChildCount(); a < N; a++) {
                    if (isViewVisible(getChildAt(a))) {
                        tabsTextWidthWithMargin[a] = share;
                    }
                }
            }
        }

        int l = 0;
        for (int a = 0, N = getChildCount(); a < N; a++) {
            if (!isViewVisible(getChildAt(a))) {
                continue;
            }

            tabsWidth[a] = Math.round(tabsTextWidthWithMargin[a]);
            tabsLeftPos[a] = l;
            l += tabsWidth[a];
        }
        setMeasuredDimension(l + getPaddingLeft() + getPaddingRight(), height);
        for (int a = 0, N = getChildCount(); a < N; a++) {
            final View child = getChildAt(a);
            child.measure(
                MeasureSpec.makeMeasureSpec(tabsWidth[a], MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(tabHeight, MeasureSpec.EXACTLY));
        }

        calculateTotalSizesAfterMeasure();
    }

    private float uniformSlotWidth(){float width=Float.MAX_VALUE;for(int i=0;i<getChildCount();i++){View c=getChildAt(i);if(isViewVisible(c)&&c.getWidth()>0)width=Math.min(width,c.getWidth());}return width==Float.MAX_VALUE?dp(64):width;}
    private float viewportOffset;
    private int flexyContentWidth;
    private boolean flexyScrollGesture;
    private boolean scrollable(){return LiquidNavigationConfig.configured()&&flexyContentWidth>getWidth()+1;}
    private void applyViewportOffset(){
        for(int i=0;i<getEntriesCount();i++){
            final ListAnimator.Entry<Holder> e=getEntry(i);View child=e.item.view;
            child.setTranslationX(getPaddingLeft()+e.getRectF().left-child.getLeft()-viewportOffset);
        }
    }
    private void scrollViewport(float offset){
        float next=Math.max(0,Math.min(Math.max(0,flexyContentWidth-getWidth()),offset));
        if(next!=viewportOffset){viewportOffset=next;applyViewportOffset();if(flexyScrollGesture){View selected=findSelectedTab();if(selected!=null)animatedLongSelectedViewCenterX=getCenterX(selected);}invalidate();}
    }
    private void ensureSelectedVisible(){
        View selected=findSelectedTab();if(selected==null||!scrollable())return;
        float left=selected.getX(),right=left+selected.getWidth();
        if(left<getPaddingLeft())scrollViewport(viewportOffset+left-getPaddingLeft());
        else if(right>getWidth()-getPaddingRight())scrollViewport(viewportOffset+right-getWidth()+getPaddingRight());
    }
    public void revealSelectedDestination(){ensureSelectedVisible();invalidate();}
    private void edgeScroll(){
        if(!flexyPressed||!flexyDragging||!scrollable())return;
        float edge=dp(32),delta=flexyFingerX<edge?-dp(3)*(1-flexyFingerX/edge):flexyFingerX>getWidth()-edge?dp(3)*(flexyFingerX-getWidth()+edge)/edge:0;
        if(delta==0)return;
        scrollViewport(viewportOffset+Math.max(-dp(4),Math.min(dp(4),delta)));
        flexyMoveDrag(flexyFingerX);postOnAnimation(edgeScroller);
    }
    private final Runnable edgeScroller=this::edgeScroll;

    public interface Tab {
        float measureTextWidth();
        default float measureTextWidth(float textSizeDp) { return measureTextWidth(); }
        default void setTextSizeDp(float textSizeDp) {}
    }



    // fills tabsTextWidth[] and return visible child count;

    private float[] tabsTextWidth;
    private float[] tabsTextWidthWithMargin;
    private int[] tabsWeight;
    private int[] tabsWidth;

    private int[] tabsLeftPos;


    private int visibleChildCount;
    private int biggestTabTextWidth;

    private void measureTabTexts(float textSizeDp) {
        final int childCount = getChildCount();
        if (tabsTextWidth == null || tabsTextWidth.length < childCount) {
            tabsTextWidth = new float[childCount];
            tabsTextWidthWithMargin = new float[childCount];
            tabsWeight = new int[childCount];
            tabsLeftPos = new int[childCount];
            tabsWidth = new int[childCount];
        }

        float maxTabWidthF = 0;
        int index = 0;

        for (int a = 0; a < childCount; a++) {
            final View child = getChildAt(a);
            if (!isViewVisible(child)) {
                tabsTextWidth[a] = -1;
                continue;
            }

            final float tabWidth;
            if (child instanceof MainTabsLayout.Tab) {
                tabWidth = ((MainTabsLayout.Tab) child).measureTextWidth(textSizeDp);
            } else {
                tabWidth = 0;
            }

            tabsTextWidth[a] = tabWidth;
            maxTabWidthF = Math.max(maxTabWidthF, tabWidth);
            index++;
        }

        biggestTabTextWidth = (int) Math.ceil(maxTabWidthF);
        visibleChildCount = index;
    }

    private void applyPassTextSize(int pass) {
        final float textSizeDp = PASS_TEXT_SIZES_DP[pass];
        for (int a = 0, N = getChildCount(); a < N; a++) {
            final View child = getChildAt(a);
            if (child instanceof MainTabsLayout.Tab) {
                ((MainTabsLayout.Tab) child).setTextSizeDp(textSizeDp);
            }
        }
    }

    @Override
    protected void setChildVisibilityFactor(View view, float factor) {
        final float s = lerp(0.7f, 1f, factor);
        view.setAlpha(factor);
        view.setScaleX(s);
        view.setScaleY(s);
    }

    @Override
    protected void onLayout(boolean changed, int l, int t, int r, int b) {
        super.onLayout(changed, l, t, r, b);
        if (changed) cancelLiquidForLayout();
        viewportOffset=Math.max(0,Math.min(viewportOffset,Math.max(0,flexyContentWidth-getWidth())));
        applyViewportOffset();ensureSelectedVisible();checkVisualWidth();
    }

    @Override
    protected void onItemsChanged() {
        super.onItemsChanged();
        if (flexyPressed || flexyDragging || flexyTracking) cancelLiquidForLayout();
        applyViewportOffset();checkVisualWidth();
    }

    private void checkVisualWidth() {
        for (int a = 0, N = getEntriesCount(); a < N; a++) {
            final ListAnimator.Entry<Holder> entry = getEntry(a);
            final float width = entry.getRectF().width();
            ((GlassTabView) entry.item.view).setVisualWidth(width);
        }
    }








    public void setTabSelected(View tab, boolean animated) {
        for (int a = 0, N = getChildCount(); a < N; a++) {
            final View child = getChildAt(a);
            if (child instanceof GlassTabView) {
                ((GlassTabView) child).setSelected(child == tab, animated);
            }
        }
        if(!flexyPressed&&!flexyDragging)ensureSelectedVisible();
    }

    private View findSelectedTab() {
        for (int a = 0, N = getChildCount(); a < N; a++) {
            final View child = getChildAt(a);
            if (child.getVisibility() != View.VISIBLE) {
                continue;
            }

            if (child instanceof GlassTabView) {
                if (((GlassTabView) child).isTabSelected()) {
                    return child;
                }
            }
        }
        return null;
    }

    private final Runnable restoreDrawSelector = () -> setSkipDrawSelector(flexyLiquidEnabled());
    private final Runnable finishNativeTap = this::finishPostedNativeTap;
    private void finishPostedNativeTap() {
        if (isAttachedToWindow() && flexyPressed && !flexyDragging) flexyFinishDrag(false);
    }
    private final LiquidLensRenderer liquidLens = new LiquidLensRenderer();
    private float flexyDirection;
    public void setLiquidLensBackground(android.graphics.drawable.Drawable value) {
        android.graphics.drawable.Drawable previous = liquidLens.backdrop();
        if (previous != null) previous.setCallback(null);
        liquidLens.backdrop(value);
        if (value != null) value.setCallback(this);
        invalidate();
    }
    @Override protected boolean verifyDrawable(@NonNull android.graphics.drawable.Drawable value) {
        return value == liquidLens.backdrop() || super.verifyDrawable(value);
    }
    private boolean liquidPreview;
    public void setLiquidPreview(boolean preview) { liquidPreview=preview; refreshLiquidAppearance(); }
    public void refreshLiquidAppearance() {
        cancelLiquidForLayout();setSkipDrawSelector(flexyLiquidEnabled());requestLayout();invalidate();
    }
    private void cancelLiquidForLayout() {
        boolean owned=flexyPressed || flexyDragging || flexyTracking;
        removeCallbacks(finishNativeTap);removeCallbacks(edgeScroller);flexyScrollGesture=false;
        flexyPressed=flexyDragging=flexyTracking=false;
        flexyPointerId=MotionEvent.INVALID_POINTER_ID;
        flexyStretch=flexyDirection=flexyExpansion=0;flexyOwnLens=false;
        if(flexyExpansionSpring!=null)flexyExpansionSpring.cancel();
        if(selectedTabPositionX!=null)selectedTabPositionX.cancel();
        if(selectedTabPositionOffsetX!=null)selectedTabPositionOffsetX.cancel();
        if(flexyDeformation!=null)flexyDeformation.cancel();
        if(owned){
            // Cancel the native child click/long press and consume the old sequence through UP.
            flexyIgnoreUntilUp=true;
            long now=android.os.SystemClock.uptimeMillis();
            MotionEvent cancel=MotionEvent.obtain(now,now,MotionEvent.ACTION_CANCEL,0,0,0);
            try{super.dispatchTouchEvent(cancel);}finally{cancel.recycle();}
        }
        View selected=findSelectedTab();
        if(selected!=null)animatedLongSelectedViewCenterX=selected.getX()+selected.getWidth()*.5f;
        animatedLongSelectedViewOffsetX=0;
    }

    private boolean drawCustomSelector;
    private void setSkipDrawSelector(boolean skipDrawSelector) {
        drawCustomSelector = skipDrawSelector;
        if (drawCustomSelector) {
            selectorPaint.setColor(Theme.multAlpha(Theme.getColor(Theme.key_glass_tabSelected, resourcesProvider), 0.09f));
        }
        for (int a = 0, N = getChildCount(); a < N; a++) {
            final View child = getChildAt(a);
            if (child.getVisibility() != View.VISIBLE) {
                continue;
            }

            if (child instanceof GlassTabView) {
                ((GlassTabView) child).setSkipDrawSelector(skipDrawSelector);
            }
        }
        invalidate();
    }







    @Override
    protected void dispatchDraw(@NonNull Canvas canvas) {
        if (flexyLiquidEnabled() && !drawCustomSelector) setSkipDrawSelector(true);
        if (drawCustomSelector) {
            if (flexyLiquidEnabled() && !flexyPressed && !flexyDragging && !selectedTabPositionX.isRunning()) {
                View selected=findSelectedTab();
                if(selected!=null) animatedLongSelectedViewCenterX=selected.getX()+selected.getWidth()*.5f;
            }
            final float x = animatedLongSelectedViewCenterX + animatedLongSelectedViewOffsetX;
            final float rawWidth = flexyLiquidEnabled()?Math.min(dp(LiquidNavigationConfig.lensWidthDp()),uniformSlotWidth()*.96f):getInterpolatedWidthByX(x, this);
            final float wantedWidth = flexyLiquidEnabled()
                    ? LiquidNavigationMath.width(rawWidth, flexyStretch) : rawWidth;
            final float room=Math.max(0,Math.min(x-getPaddingLeft(),getWidth()-getPaddingRight()-x))*2f;
            final float sWidth=flexyLiquidEnabled() ? Math.min(wantedWidth,room) : wantedWidth;
            if (flexyLiquidEnabled()) {
                float expansion=LiquidNavigationConfig.expansion()?Math.max(0,Math.min(1.12f,flexyExpansion)):0;
                float lensHeight=Math.min(dp(LiquidNavigationConfig.lensHeightDp()),rawWidth/1.55f);
                float expandedHeight=lensHeight+expansion*dp(16+LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.EXPAND_Y)*.14f);
                float expandedWidth=rawWidth*(1+expansion*(.16f+LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.EXPAND_X)*.006f));
                // Lens can overhang the fixed capsule vertically; its own frame reserves room.
                // Width is destination independent, and aspect ratio stays horizontal at all settings.
                float safeWidth=Math.min(getWidth()-dp(2),uniformSlotWidth()+2f*Math.min(getPaddingLeft(),getPaddingRight())-dp(2));
                expandedWidth=Math.min(safeWidth,Math.max(expandedWidth,expandedHeight*1.55f)*(1+Math.min(.14f,flexyStretch)));
                expandedHeight=Math.min(expandedHeight,Math.min(getHeight()-dp(2),expandedWidth/1.55f));
                float lensX=x;
                liquidLens.prepare(lensX,getHeight()*.5f,expandedWidth,expandedHeight,flexyStretch,flexyDirection);
                liquidLens.surface(canvas);
            } else if (MainTabsUiHelper.isMaterial3NavigationBar()) {
                MainTabsUiHelper.setMainTabSelectedIndicatorBounds(selectorRect, sWidth,
                        getHeight() - getPaddingTop() - getPaddingBottom());
                selectorRect.offset(x - sWidth / 2f, getPaddingTop());
                final float r = selectorRect.height() / 2f;
                canvas.drawRoundRect(selectorRect, r, r, selectorPaint);
            } else {
                final float sHeight = getHeight() - getPaddingTop() - getPaddingBottom();
                canvas.drawRoundRect(
                        x - sWidth / 2f, (getHeight() - sHeight) / 2f,
                        x + sWidth / 2f, (getHeight() + sHeight) / 2f,
                        sHeight * LiquidNavigationMath.compression(flexyStretch) / 2f,
                        sHeight * LiquidNavigationMath.compression(flexyStretch) / 2f,
                        selectorPaint);
            }
        }

        if (drawCustomSelector && flexyLiquidEnabled()) {
            // Draw each visible pixel of the content once: unmagnified outside, refracted inside.
            int outside=canvas.save();
            canvas.clipPath(liquidLens.shape(),android.graphics.Region.Op.DIFFERENCE);
            super.dispatchDraw(canvas);
            canvas.restoreToCount(outside);
            int inside=canvas.save();
            canvas.clipPath(liquidLens.shape());
            float magnification=liquidLens.magnification();
            canvas.scale(magnification,magnification,
                    animatedLongSelectedViewCenterX+animatedLongSelectedViewOffsetX,getHeight()*.5f);
            super.dispatchDraw(canvas);
            canvas.restoreToCount(inside);
            liquidLens.rim(canvas,getResources().getDisplayMetrics().density);
        } else super.dispatchDraw(canvas);

        if (drawTopDivider && MainTabsUiHelper.isMaterial3NavigationBar()) {
            dividerPaint.setColor(Theme.getDividerColor(resourcesProvider));
            canvas.drawLine(0, 1, getMeasuredWidth(), 1, dividerPaint);
        }
    }

    private boolean drawTopDivider = true;

    public void setDrawTopDivider(boolean value) {
        if (drawTopDivider != value) {
            drawTopDivider = value;
            invalidate();
        }
    }

    final Paint dividerPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    final Paint selectorPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final android.graphics.RectF selectorRect = new android.graphics.RectF();
    final SpringAnimation scaleX = new SpringAnimation(this, DynamicAnimation.SCALE_X, 1f);
    final SpringAnimation scaleY = new SpringAnimation(this, DynamicAnimation.SCALE_Y, 1f);

    final SpringAnimation selectedTabPositionOffsetX = new SpringAnimation(this, new FloatPropertyCompat<MainTabsLayout>("selectedTabPositionOffsetX") {
        @Override
        public float getValue(MainTabsLayout object) {
            return object.animatedLongSelectedViewOffsetX;
        }

        @Override
        public void setValue(MainTabsLayout object, float value) {
            object.animatedLongSelectedViewOffsetX = value;
            object.invalidate();
        }
    });
    final SpringAnimation selectedTabPositionX = new SpringAnimation(this, new FloatPropertyCompat<MainTabsLayout>("selectedTabPositionX") {
        @Override
        public float getValue(MainTabsLayout object) {
            return object.animatedLongSelectedViewCenterX;
        }

        @Override
        public void setValue(MainTabsLayout object, float value) {
            object.animatedLongSelectedViewCenterX = value;
            object.invalidate();
        }
    });

    {
        selectedTabPositionOffsetX.setSpring(new SpringForce(1)
            .setStiffness(SpringForce.STIFFNESS_MEDIUM)
            .setDampingRatio(SpringForce.DAMPING_RATIO_LOW_BOUNCY));
        scaleX.setSpring(new SpringForce(1f)
            .setStiffness(250)
            .setDampingRatio(0.25f));
        scaleY.setSpring(new SpringForce(1f)
            .setStiffness(250)
            .setDampingRatio(0.25f));
        selectedTabPositionX.setSpring(new SpringForce(1f)
            .setStiffness(SpringForce.STIFFNESS_MEDIUM)
            .setDampingRatio(SpringForce.DAMPING_RATIO_LOW_BOUNCY));
    }

    private float animatedLongSelectedViewCenterX;
    private float animatedLongSelectedViewOffsetX;

    // Direct drag gesture, independent from legacy long-press clickHelper.
    private boolean flexyOwnLens;
    private float flexyExpansion;
    private final SpringAnimation flexyExpansionSpring=new SpringAnimation(this,new FloatPropertyCompat<MainTabsLayout>("lensExpansion"){
        public float getValue(MainTabsLayout v){return v.flexyExpansion;}
        public void setValue(MainTabsLayout v,float value){v.flexyExpansion=value;v.invalidate();}
    }).setMinimumVisibleChange(.001f);
    private void expandLens(boolean pressed){
        flexyExpansionSpring.cancel();
        if(pressed)flexyExpansion=Math.max(.12f,flexyExpansion);
        flexyExpansionSpring.setSpring(new SpringForce(pressed?1:0).setStiffness(LiquidNavigationConfig.stiffness()).setDampingRatio(LiquidNavigationConfig.damping()));
        flexyExpansionSpring.animateToFinalPosition(pressed?1:0);invalidate();
    }
    private boolean flexyDragging, flexyTracking, flexyEligible, flexyPressed, flexyIgnoreUntilUp;
    private int flexyPointerId = MotionEvent.INVALID_POINTER_ID;
    private float flexyDownX, flexyDownY, flexyPreviousX, flexyStretch, flexyFingerX;
    private long flexyEventTime, flexyPreviousEventTime;
    private final int flexyTouchSlop = ViewConfiguration.get(getContext()).getScaledTouchSlop();
    private boolean flexyLiquidEnabled() {
        return LiquidNavigationConfig.enabled() && getVisibility() == View.VISIBLE && isEnabled()
                && !isInLongPress;
    }
    private void flexyBeginDrag(float x) {
        flexyPressed = true;
        expandLens(true);
        selectedTabPositionX.cancel();
        selectedTabPositionOffsetX.cancel();
        animatedLongSelectedViewCenterX = clampXToChildrenCenters(x, this);
        animatedLongSelectedViewOffsetX = 0f;
        flexyPreviousX = flexyFingerX = x;
        flexyPreviousEventTime=flexyEventTime;
        flexyDeformation.cancel();
        flexyStretch = 0f;
        flexyDirection = 0f;
        AndroidUtilities.cancelRunOnUIThread(restoreDrawSelector);
        setSkipDrawSelector(true);
    }
    private void flexyMoveDrag(float x) {
        final float clamped = clampXToChildrenCenters(x, this);
        final float width = Math.max(1f, getInterpolatedWidthByX(clamped, this));
        float interval=Math.max(1L,flexyEventTime-flexyPreviousEventTime);
        float normalizedDistance=(clamped-flexyPreviousX)*16f/interval;
        if (normalizedDistance != 0f) flexyDirection=Math.signum(normalizedDistance);
        normalizedDistance *= .65f+LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.FOLLOW)*.0035f;
        flexyPreviousEventTime=flexyEventTime;
        flexyStretch = LiquidNavigationMath.stretch(normalizedDistance, width,
                LiquidNavigationConfig.elasticity()
                * LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.DEFORMATION)/100f);
        flexyPreviousX = clamped;
        animatedLongSelectedViewCenterX = clamped;
        animatedLongSelectedViewOffsetX = 0f;
        invalidate();
    }
    private final SpringAnimation flexyDeformation = new SpringAnimation(this,
            new FloatPropertyCompat<MainTabsLayout>("flexyDeformation") {
                public float getValue(MainTabsLayout v){return v.flexyStretch;}
                public void setValue(MainTabsLayout v,float value){v.flexyStretch=Math.max(0,value);v.invalidate();}
            }).setMinimumVisibleChange(.001f);
    private void flexyFinishDrag(boolean cancelled) {
        if (!flexyPressed && !flexyDragging) return;
        boolean commit = flexyDragging && !cancelled;
        expandLens(false);removeCallbacks(edgeScroller);
        flexyDragging = flexyPressed = flexyTracking = false;
        View target = commit ? findNearestVisibleChildByX(flexyFingerX,this) : findSelectedTab();
        if (commit && target != null && target != findSelectedTab()) target.performClick();
        // A rejected navigation or shortcut leaves native selection authoritative.
        View selected=findSelectedTab();
        if (selected != null) target=selected;
        if (target != null) {
            final float center=target.getX()+target.getWidth()*.5f;
            float pace=310f/LiquidNavigationConfig.settleMillis();
            float damping=Math.max(.65f,LiquidNavigationConfig.damping()
                    -LiquidNavigationConfig.value(LiquidNavigationConfig.Parameter.REBOUND)*.002f);
            selectedTabPositionX.setSpring(new SpringForce(center)
                    .setStiffness(LiquidNavigationConfig.stiffness()*pace*pace).setDampingRatio(damping));
            selectedTabPositionX.animateToFinalPosition(center);
            flexyDeformation.setSpring(new SpringForce(0).setStiffness(LiquidNavigationConfig.stiffness()).setDampingRatio(damping));
            flexyDeformation.animateToFinalPosition(0);
        }
        if(!flexyScrollGesture)ensureSelectedVisible();
        AndroidUtilities.cancelRunOnUIThread(restoreDrawSelector);
        invalidate();
    }
    private boolean isInLongPress;
    private float lastLongSelectedViewCenterX;
    private float lastLongSelectedViewWidth;
    private View lastLongSelectedView;




    public static View findChildUnder(ViewGroup parent, float x, float y) {
        for (int i = parent.getChildCount() - 1; i >= 0; i--) {
            View child = parent.getChildAt(i);

            if (child.getVisibility() != View.VISIBLE) continue;

            if (x >= child.getX() && x <= child.getX()+child.getWidth()
                    && y >= child.getY() && y <= child.getY()+child.getHeight()) {
                return child;
            }
        }
        return null;
    }

    private void checkLongMove(float x_, float y, boolean start, boolean end) {
        final float x = clampXToChildrenCenters(x_, this);
        final View found = findNearestVisibleChildByX(x, this);
        if (start) {
            View selected = findSelectedTab();
            if (selected != null) {
                animatedLongSelectedViewCenterX = selected.getX() + selected.getWidth() / 2f;
                animatedLongSelectedViewOffsetX = animatedLongSelectedViewCenterX - x;
                selectedTabPositionOffsetX.animateToFinalPosition(0);
                if (selected != found && found != null) {
                    found.performClick();
                }
            }
            selectedTabPositionX.cancel();
        }

        if (!end) {
            animatedLongSelectedViewCenterX = x;
            invalidate();
        }

        if (found != null) {
            lastLongSelectedView = found;
            setTabSelected(found, true);

            if (end) {
                final float vw = found.getWidth();
                final float cx = found.getX() + vw / 2f;
                if (lastLongSelectedViewWidth != vw || lastLongSelectedViewCenterX != cx) {
                    selectedTabPositionX.animateToFinalPosition(cx);
                }
            }
        }
    }

    private final Set<View> tabsWithIgnoreClick = new HashSet<>();
    public void addTabToIgnoreClick(View v) {
        tabsWithIgnoreClick.add(v);
    }

    private final BoolAnimator animatorIsScaled = new BoolAnimator(0, (a, factor, c, g) -> {
        setScaleX(lerp(1, 1.019f, factor));
        setScaleY(lerp(1, 1.019f, factor));
    }, CubicBezierInterpolator.EASE_OUT_QUINT, 380);

    private final ClickHelper clickHelper = new ClickHelper(new ClickHelper.Delegate() {
        @Override
        public boolean needClickAt(View view, float x, float y) {
            lastLongSelectedView = null;
            final View found = findChildUnder(MainTabsLayout.this, x, y);
            return found != null && !tabsWithIgnoreClick.contains(found);
        }

        @Override
        public void onClickAt(View view, float x, float y) {
        }

        @Override
        public boolean needLongPress(float x, float y) {
            return true;
        }

        @Override
        public boolean needCancelTouchBySlopMove() {
            return false;
        }


        @Override
        public boolean onLongPressRequestedAt(View view, float x, float y) {
            checkPivot(view, x, y);
            isInLongPress = true;
            AndroidUtilities.cancelRunOnUIThread(restoreDrawSelector);
            setSkipDrawSelector(true);
            checkLongMove(x, y, true, false);
            invalidate();
            longTouchStart();
            return true;
        }

        @Override
        public void onLongPressMove(View view, MotionEvent e, float x, float y, float startX, float startY) {
            checkPivot(view, x, y);
            checkLongMove(x, y, false, false);
            invalidate();
        }

        @Override
        public long getLongPressDuration() {
            return ClickHelper.Delegate.super.getLongPressDuration() * 750 / 1000;
        }

        @Override
        public void onLongPressFinish(View view, float x, float y) {
            checkPivot(view, x, y);
            checkLongMove(x, y, false, true);
            isInLongPress = false;
            AndroidUtilities.runOnUIThread(restoreDrawSelector, 450);
            if (lastLongSelectedView != null) {
                lastLongSelectedView.performClick();
            }
            lastLongSelectedView = null;
            invalidate();
            longTouchEnd();
        }

        @Override
        public void onLongPressCancelled(View view, float x, float y) {
            checkPivot(view, x, y);
            checkLongMove(x, y, false, true);
            isInLongPress = false;
            AndroidUtilities.runOnUIThread(restoreDrawSelector, 450);
            lastLongSelectedView = null;
            invalidate();
            longTouchEnd();
        }

        private void longTouchStart() {
            animatorIsScaled.setValue(true, true);

            /*
            if (!scaleX.isRunning()) {
                scaleX.setStartVelocity(-0.45f);
                scaleY.setStartVelocity(-0.45f);
            }
            scaleX.animateToFinalPosition(1.012f);
            scaleY.animateToFinalPosition(1.012f);
            */
        }

        private void longTouchEnd() {
            animatorIsScaled.setValue(false, true);

            /*
            if (!scaleX.isRunning()) {
                scaleX.setStartVelocity(0.25f);
                scaleY.setStartVelocity(0.25f);
            }
            scaleX.animateToFinalPosition(1f);
            scaleY.animateToFinalPosition(1f);
            */
        }
    });

    @Override
    public void setScaleY(float scaleY) {
        super.setScaleY(scaleY);
        checkLayerType();
    }

    @Override
    public void setScaleX(float scaleX) {
        super.setScaleX(scaleX);
        checkLayerType();
    }

    private void checkLayerType() {
        final int layerType = Math.abs(getScaleX() - 1f) < 0.0001f && Math.abs(getScaleY() - 1f) < 0.0001f ?
            View.LAYER_TYPE_NONE : View.LAYER_TYPE_HARDWARE;

        if (getLayerType() != layerType) {
            setLayerType(layerType, null);
            invalidate();
        }
    }


    private void checkPivot(View view, float x, float y) {
        float w = view.getWidth();
        float h = view.getHeight();

        if (w <= 0f || h <= 0f) {
            return;
        }

        float cx = w * 0.5f;
        float cy = h * 0.5f;

        float dx = x - cx;
        float dy = y - cy;

        float halfW = w * 0.5f;
        float halfH = h * 0.5f;

        float nx = dx / halfW;
        float ny = dy / halfH;

        float r = (float) Math.sqrt(nx * nx + ny * ny);

        float pivotX;
        float pivotY;

        if (r > 1e-4f) {
            float mappedR = 1.5f * r / (r + 0.5f);

            float scale = mappedR / r;
            pivotX = cx + dx * scale;
            pivotY = cy + dy * scale;
        } else {
            pivotX = cx;
            pivotY = cy;
        }

        pivotX = lerp(cx, pivotX, 1f);
        pivotY = lerp(cy, pivotY, 3f);

        view.setPivotX(pivotX);
        view.setPivotY(pivotY);
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {
        if (!flexyLiquidEnabled()) return super.onInterceptTouchEvent(ev);
        final int action = ev.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            flexyTracking = true;
            flexyDragging = false;
            flexyPointerId = ev.getPointerId(0);
            flexyDownX = flexyPreviousX = ev.getX();
            flexyDownY = ev.getY();
            flexyEligible = findChildUnder(this, flexyDownX, flexyDownY) != null;
            return flexyOwnLens;
        }
        if (action == MotionEvent.ACTION_MOVE && flexyTracking && flexyEligible) {
            final int p = ev.findPointerIndex(flexyPointerId);
            if (p < 0) return false;
            final float dx = ev.getX(p) - flexyDownX;
            final float dy = ev.getY(p) - flexyDownY;
            if (Math.abs(dx) > flexyTouchSlop &&
                    Math.abs(dx) > Math.abs(dy) * 1.1f) {
                if(scrollable()&&!flexyOwnLens){flexyScrollGesture=true;flexyDragging=false;expandLens(false);}
                else flexyDragging = true;
                return true; // cancels the child click without waiting for a long press
            }
        }
        return super.onInterceptTouchEvent(ev);
    }
    @Override
    public boolean onTouchEvent(MotionEvent ev) {
        if(flexyScrollGesture){
            int action=ev.getActionMasked();
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){flexyFinishDrag(true);flexyScrollGesture=false;}
            return true;
        }
        if (flexyDragging || flexyOwnLens) {
            final int action = ev.getActionMasked();
            if (action == MotionEvent.ACTION_POINTER_DOWN || action == MotionEvent.ACTION_POINTER_UP) {
                flexyFinishDrag(true);return true;
            }
            if (action == MotionEvent.ACTION_MOVE) {
                int pointer = ev.findPointerIndex(flexyPointerId);
                if (pointer < 0) { flexyFinishDrag(true); return true; }
                // dispatchTouchEvent already consumes this MOVE once, including its velocity.
                return true;
            } else if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                if (action == MotionEvent.ACTION_UP) {
                    animatedLongSelectedViewCenterX=clampXToChildrenCenters(ev.getX(),this);
                }
                if(action==MotionEvent.ACTION_UP && flexyOwnLens && !flexyDragging){View selected=findSelectedTab();if(selected!=null)selected.performClick();}
                flexyOwnLens=false;
                flexyFinishDrag(action == MotionEvent.ACTION_CANCEL);
                flexyTracking = false;
                flexyPointerId = MotionEvent.INVALID_POINTER_ID;
                return true;
            }
            return true;
        }
        return super.onTouchEvent(ev);
    }
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        if (!LiquidNavigationConfig.enabled()) {
            if (flexyPressed || flexyDragging) flexyFinishDrag(true);
            clickHelper.onTouchEvent(this, ev);
            return super.dispatchTouchEvent(ev);
        }
        int action=ev.getActionMasked();
        flexyEventTime=ev.getEventTime();
        int ownedPointer=ev.findPointerIndex(flexyPointerId);
        if(action==MotionEvent.ACTION_DOWN)flexyFingerX=ev.getX();
        else if(ownedPointer>=0)flexyFingerX=ev.getX(ownedPointer);
        if(action==MotionEvent.ACTION_DOWN){removeCallbacks(finishNativeTap);flexyIgnoreUntilUp=false;}
        if(flexyIgnoreUntilUp)return true;
        if(action==MotionEvent.ACTION_POINTER_DOWN || action==MotionEvent.ACTION_POINTER_UP
                || action==MotionEvent.ACTION_MOVE && flexyPressed
                && Math.abs(ev.getY()-flexyDownY)>flexyTouchSlop
                && Math.abs(ev.getY()-flexyDownY)>Math.abs(ev.getX()-flexyDownX)*1.1f) {
            flexyFinishDrag(true);flexyIgnoreUntilUp=true;
            MotionEvent cancel=MotionEvent.obtain(ev);cancel.setAction(MotionEvent.ACTION_CANCEL);
            try {super.dispatchTouchEvent(cancel);}finally{cancel.recycle();}
            return true;
        }
        if(action==MotionEvent.ACTION_DOWN && findChildUnder(this,ev.getX(),ev.getY())!=null) {
            View selected=findSelectedTab();
            flexyOwnLens=selected!=null && Math.abs(ev.getX()-getCenterX(selected))<=dp(LiquidNavigationConfig.lensWidthDp())*.5f;
            flexyBeginDrag(ev.getX()); // Native child clicks remain authoritative away from selected lens.
        } else if(action==MotionEvent.ACTION_MOVE && flexyPressed) {
            int pointer=ev.findPointerIndex(flexyPointerId);
            if(pointer>=0) {
                float x=ev.getX(pointer);
                if(flexyScrollGesture){scrollViewport(viewportOffset+flexyPreviousX-x);flexyPreviousX=x;}
                else{
                    if(flexyOwnLens && Math.abs(x-flexyDownX)>flexyTouchSlop)flexyDragging=true;
                    flexyMoveDrag(x);
                    removeCallbacks(edgeScroller);if(flexyDragging)postOnAnimation(edgeScroller);
                }
            }
        } else if(action==MotionEvent.ACTION_POINTER_DOWN || action==MotionEvent.ACTION_POINTER_UP) {
            flexyFinishDrag(true);
        }
        boolean result=super.dispatchTouchEvent(ev);
        if(action==MotionEvent.ACTION_UP || action==MotionEvent.ACTION_CANCEL) {
            if (action==MotionEvent.ACTION_UP && flexyPressed && !flexyDragging) {
                // Android posts the child's native click. Settle after that same queue turn,
                // so a normal tap cannot spring back to the previously selected tab.
                post(finishNativeTap);
            } else flexyFinishDrag(action==MotionEvent.ACTION_CANCEL);
            flexyPointerId=MotionEvent.INVALID_POINTER_ID;
        }
        return result;
    }
    @Override protected void onVisibilityChanged(@NonNull View changed, int visibility) {
        super.onVisibilityChanged(changed, visibility);
        if (visibility != VISIBLE) {
            removeCallbacks(finishNativeTap);removeCallbacks(edgeScroller);flexyScrollGesture=false;
            flexyDragging=flexyPressed=flexyTracking=false;flexyPointerId=MotionEvent.INVALID_POINTER_ID;
            flexyStretch=flexyExpansion=0;flexyOwnLens=false;
            if(flexyExpansionSpring!=null)flexyExpansionSpring.cancel();
            if (selectedTabPositionX != null) selectedTabPositionX.cancel();
            if (flexyDeformation != null) flexyDeformation.cancel();
        }
    }
    @Override protected void onDetachedFromWindow() {
        removeCallbacks(finishNativeTap);removeCallbacks(edgeScroller);flexyScrollGesture=false;
        flexyDragging=flexyPressed=flexyTracking=flexyIgnoreUntilUp=false;
        flexyPointerId=MotionEvent.INVALID_POINTER_ID;flexyStretch=flexyExpansion=0;flexyOwnLens=false;flexyExpansionSpring.cancel();
        selectedTabPositionX.cancel();selectedTabPositionOffsetX.cancel();flexyDeformation.cancel();
        AndroidUtilities.cancelRunOnUIThread(restoreDrawSelector);
        super.onDetachedFromWindow();
    }


    private static float clampXToChildrenCenters(float x, ViewGroup parent) {
        if (parent == null || parent.getChildCount() == 0) {
            return x;
        }

        float min = Float.MAX_VALUE;
        float max = -Float.MAX_VALUE;
        boolean found = false;

        for (int i = 0; i < parent.getChildCount(); i++) {
            View view = parent.getChildAt(i);
            if (view == null || view.getVisibility() != View.VISIBLE) {
                continue;
            }

            float centerX = view.getX() + view.getWidth() * 0.5f;

            if (centerX < min) min = centerX;
            if (centerX > max) max = centerX;

            found = true;
        }

        if (!found) {
            return x;
        }

        if (x < min) return min;
        if (x > max) return max;
        return x;
    }

    @Nullable
    private static View findNearestVisibleChildByX(float x, ViewGroup parent) {
        if (parent == null || parent.getChildCount() == 0) {
            return null;
        }

        View nearest = null;
        float nearestDistance = Float.MAX_VALUE;

        for (int i = 0; i < parent.getChildCount(); i++) {
            View view = parent.getChildAt(i);
            if (view == null || view.getVisibility() != View.VISIBLE) {
                continue;
            }

            float centerX = view.getX() + view.getWidth() * 0.5f;
            float distance = Math.abs(centerX - x);

            if (distance < nearestDistance) {
                nearestDistance = distance;
                nearest = view;
            }
        }

        return nearest;
    }

    private static float getInterpolatedWidthByX(float x, ViewGroup parent) {
        if (parent == null || parent.getChildCount() == 0) {
            return 0f;
        }

        View left = null;
        View right = null;

        for (int i = 0; i < parent.getChildCount(); i++) {
            View view = parent.getChildAt(i);
            if (view == null || view.getVisibility() != View.VISIBLE) {
                continue;
            }

            float centerX = view.getX() + view.getWidth() * 0.5f;

            if (centerX <= x && (left == null || centerX > getCenterX(left))) {
                left = view;
            }

            if (centerX >= x && (right == null || centerX < getCenterX(right))) {
                right = view;
            }
        }

        if (left == null && right == null) {
            return 0f;
        }

        if (left == null) {
            return right.getWidth();
        }

        if (right == null) {
            return left.getWidth();
        }

        float leftX = getCenterX(left);
        float rightX = getCenterX(right);

        if (left == right || leftX == rightX) {
            return left.getWidth();
        }

        float ratio = (x - leftX) / (rightX - leftX);
        return lerp(left.getWidth(), right.getWidth(), ratio);
    }

    private static float getCenterX(View v) {
        return v.getX() + v.getWidth() * 0.5f;
    }
}
