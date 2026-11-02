package org.telegram.ui;

import static org.telegram.messenger.AndroidUtilities.dp;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import android.view.ViewGroup;
import android.graphics.drawable.GradientDrawable;
import androidx.annotation.NonNull;
import androidx.dynamicanimation.animation.FloatPropertyCompat;
import androidx.dynamicanimation.animation.SpringAnimation;
import androidx.dynamicanimation.animation.SpringForce;
import app.flexygram.navigation.LiquidNavigationConfig;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.AnimatedLinearLayout;
import org.telegram.ui.Components.glass.GlassTabView;
import tw.nekomimi.nekogram.NekoConfig;
import xyz.nextalone.nagram.NaConfig;

/** Native blur3 dock with solid fallback. Equal slots and no idle render loop. */
public class MainTabsLayout extends AnimatedLinearLayout {
    public static final int BOTTOM_NAVIGATION_MODE_SHOW = 0;
    public static final int BOTTOM_NAVIGATION_MODE_HIDE = 1;
    public static final int BOTTOM_NAVIGATION_MODE_FLOATING = 2;

    public static int getBottomNavigationMode() { return BOTTOM_NAVIGATION_MODE_SHOW; }
    public static boolean isBottomNavigationHidden() { return false; }
    public static boolean isBottomNavigationVisible() { return true; }
    public static boolean isBottomNavigationFloating() { return false; }

    public interface Tab {
        float measureTextWidth();
        default float measureTextWidth(float size){return measureTextWidth();}
        default void setTextSizeDp(float size){}
    }
    private final Theme.ResourcesProvider resourcesProvider;
    private final GradientDrawable surface=new GradientDrawable();
    private org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable glassBackground;
    private float glassRadius = -1;
    public void setGlassBackground(org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable drawable) {
        glassBackground = drawable; glassRadius = -1; if (drawable != null) drawable.setCallback(this); setBackground(null); setWillNotDraw(false); invalidate();
    }
    @Override protected boolean verifyDrawable(android.graphics.drawable.Drawable who) { return who == glassBackground || super.verifyDrawable(who); }
    @Override protected void onDraw(Canvas canvas) {
        if (glassBackground != null && canvas.isHardwareAccelerated()
                && org.telegram.messenger.SharedConfig.chatBlurEnabled()
                && org.telegram.messenger.LiteMode.isEnabled(org.telegram.messenger.LiteMode.FLAG_LIQUID_GLASS)) {
            float radius = dp(LiquidNavigationConfig.radiusDp());
            if (glassRadius != radius) { glassRadius = radius; glassBackground.setRadius(radius); }
            glassBackground.setBounds(0,0,getWidth(),getHeight());
            glassBackground.draw(canvas);
        } else { surface.setBounds(0,0,getWidth(),getHeight()); surface.draw(canvas); }
        super.onDraw(canvas);
    }
    private final Paint selector=new Paint(Paint.ANTI_ALIAS_FLAG);
    private float selectionX=Float.NaN;
    private int maxWidthPx,slotWidth;
    private boolean drawTopDivider=true;
    private final SpringAnimation selection=new SpringAnimation(this,new FloatPropertyCompat<MainTabsLayout>("bottomSelection"){
        public float getValue(MainTabsLayout v){return Float.isNaN(v.selectionX)?0:v.selectionX;}
        public void setValue(MainTabsLayout v,float value){v.selectionX=value;v.invalidate();}
    }).setMinimumVisibleChange(.5f);
    public MainTabsLayout(Context context,Theme.ResourcesProvider provider){
        super(context);resourcesProvider=provider;setClipChildren(true);setClipToPadding(true);setWillNotDraw(false);
        selection.setSpring(new SpringForce(0).setStiffness(650).setDampingRatio(1));
    }
    public void setMaxWidth(int width){if(maxWidthPx!=width){maxWidthPx=width;requestLayout();}}
    public void refreshBottomBarAppearance(){
        selection.cancel();selectionX=Float.NaN;
        surface.setColor(Theme.getColor(Theme.key_windowBackgroundWhite,resourcesProvider));
        surface.setCornerRadius(dp(LiquidNavigationConfig.radiusDp()));
        for(int i=0;i<getChildCount();i++)if(getChildAt(i) instanceof GlassTabView)((GlassTabView)getChildAt(i)).setSkipDrawSelector(true);
        if (glassBackground != null) glassBackground.updateColors();
        requestLayout();invalidate();
    }
    @Override protected void onMeasure(int ws,int hs){
        int available=MeasureSpec.getSize(ws);if(maxWidthPx>0)available=Math.min(available,maxWidthPx);
        int count=0;for(int i=0;i<getChildCount();i++)if(isViewVisible(getChildAt(i)))count++;
        int padding=getPaddingLeft()+getPaddingRight();
        int width=Math.min(available,Math.max(dp(48)*count+padding,Math.round(available*LiquidNavigationConfig.widthFraction())));
        int inner=Math.max(0,width-padding),height=MeasureSpec.getSize(hs);
        int content=Math.max(0,height-getPaddingTop()-getPaddingBottom());
        slotWidth=inner/Math.max(1,count);int rank=0;
        boolean hide=LiquidNavigationConfig.hideLabels(count,(int)(inner/getResources().getDisplayMetrics().density))
                ||getResources().getConfiguration().fontScale>1.3f
                ||content<dp(37+LiquidNavigationConfig.labelGapDp());
        for(int i=0;i<getChildCount();i++){
            View child=getChildAt(i);int w=isViewVisible(child)?slotWidth+(rank++<inner%Math.max(1,count)?1:0):0;
            if(child instanceof GlassTabView){
                GlassTabView tab=(GlassTabView)child;tab.setSkipDrawSelector(true);tab.setTextSizeDp(11);
                tab.setMainTabsAppearance(hide,LiquidNavigationConfig.iconDp());
            }
            child.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(content,MeasureSpec.EXACTLY));
        }
        setMeasuredDimension(width,height);calculateTotalSizesAfterMeasure();
    }
    @Override protected void setChildVisibilityFactor(View v,float factor){v.setAlpha(factor);v.setScaleX(1);v.setScaleY(1);}
    @Override protected void onItemsChanged(){
        super.onItemsChanged();
        for(int i=0;i<getEntriesCount();i++){var e=getEntry(i);if(e.item.view instanceof GlassTabView)((GlassTabView)e.item.view).setVisualWidth(e.getRectF().width());}
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        super.onLayout(changed,l,t,r,b);if(changed){selection.cancel();selectionX=Float.NaN;}
        updateSelection(false);
    }
    private View selected(){for(int i=0;i<getChildCount();i++){View v=getChildAt(i);if(isViewVisible(v)&&v instanceof GlassTabView&&((GlassTabView)v).isTabSelected())return v;}return null;}
    public void setTabSelected(View tab,boolean animated){for(int i=0;i<getChildCount();i++)if(getChildAt(i) instanceof GlassTabView)((GlassTabView)getChildAt(i)).setSelected(getChildAt(i)==tab,animated);updateSelection(animated);}
    public void revealSelectedDestination(){updateSelection(true);}
    private void updateSelection(boolean animated){
        View v=selected();if(v==null||v.getWidth()==0)return;float x=v.getX()+v.getWidth()*.5f;
        if(!animated||Float.isNaN(selectionX)||!LiquidNavigationConfig.animation()
                ||android.os.Build.VERSION.SDK_INT>=26&&!android.animation.ValueAnimator.areAnimatorsEnabled()){
            selection.cancel();selectionX=x;
        }else if(Math.abs(x-selectionX)>.5f){selection.getSpring().setStiffness(LiquidNavigationConfig.stiffness()).setDampingRatio(LiquidNavigationConfig.damping());selection.animateToFinalPosition(x);}
        invalidate();
    }
    public void addTabToIgnoreClick(View v){} // Native child click/long-click owns all gestures.
    public void setDrawTopDivider(boolean value){drawTopDivider=value;invalidate();}
    @Override protected void dispatchDraw(@NonNull Canvas canvas){
        View v=selected();if(v!=null&&slotWidth>0){
            float x=selection.isRunning()?selectionX:v.getX()+v.getWidth()*.5f;
            float w=Math.max(0,slotWidth-dp(8)),h=getHeight()-getPaddingTop()-getPaddingBottom()-dp(6);
            float y=(getPaddingTop()+getHeight()-getPaddingBottom())*.5f;
            selector.setColor(Theme.multAlpha(Theme.getColor(Theme.key_glass_tabSelected,resourcesProvider),.12f));
            float radius=Math.min(dp(LiquidNavigationConfig.radiusDp()),h*.5f);
            canvas.drawRoundRect(x-w*.5f,y-h*.5f,x+w*.5f,y+h*.5f,radius,radius,selector);
        }
        super.dispatchDraw(canvas);
    }
    @Override protected void onVisibilityChanged(@NonNull View changed,int visibility){super.onVisibilityChanged(changed,visibility);if(visibility!=VISIBLE&&selection!=null){selection.cancel();selectionX=Float.NaN;}}
    @Override protected void onDetachedFromWindow(){selection.cancel();selectionX=Float.NaN;super.onDetachedFromWindow();}
    public static View findChildUnder(ViewGroup parent,float x,float y){for(int i=parent.getChildCount()-1;i>=0;i--){View v=parent.getChildAt(i);if(v.getVisibility()==VISIBLE&&x>=v.getX()&&x<v.getX()+v.getWidth()&&y>=v.getY()&&y<v.getY()+v.getHeight())return v;}return null;}
}
