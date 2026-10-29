/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;
import android.content.Context;
import android.widget.FrameLayout;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.glass.GlassTabView;
import org.telegram.ui.MainTabsLayout;

/** The real native bar, views and gesture implementation; preview clicks only change selection. */
public final class LiquidNavigationPreviewView extends FrameLayout implements Theme.Colorable {
    private final MainTabsLayout bar;
    private final android.graphics.drawable.GradientDrawable surface=new android.graphics.drawable.GradientDrawable();
    private final GlassTabView[] tabs=new GlassTabView[10];
    private org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable nativeSurface, nativeLens;
    private final android.graphics.Paint samplePaint=new android.graphics.Paint();
    private int selected;
    private int[] lastShown=new int[0];
    private final Runnable afterSize=()->{if(isAttachedToWindow())settingsChanged();};
    public void motionSettingsChanged(){bar.invalidate();}
    public LiquidNavigationPreviewView(Context context){
        super(context);setMinimumHeight(AndroidUtilities.dp(120));
        bar=new MainTabsLayout(context,null);bar.setLiquidPreview(true);
        surface.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));bar.setBackground(surface);
        app.exteraless.appearance.MainTabsUiHelper.applyTabsLayoutStyle(bar,0);
        addView(bar,LayoutHelper.createFrame(-2,80,android.view.Gravity.CENTER));
        for(int id=0;id<tabs.length;id++){
            tabs[id]=LiquidNavigationTabs.create(context,null,UserConfig.selectedAccount,id);
            final int chosen=id;tabs[id].setOnClickListener(v->{selected=chosen;updateSelection();});
            bar.addView(tabs[id]);bar.addTabToIgnoreClick(tabs[id]);
        }
        setupNativePreviewSource();
        settingsChanged();
    }
    private void setupNativePreviewSource(){
        if(android.os.Build.VERSION.SDK_INT<31)return;
        var source=new org.telegram.ui.Components.blur3.source.BlurredBackgroundSourceRenderNode(null);
        source.setupRenderer(new org.telegram.ui.Components.blur3.RenderNodeWithHash.Renderer(){
            public void renderNodeCalculateHash(org.telegram.ui.Components.blur3.capture.IBlur3Hash hash){
                hash.add(getWidth());hash.add(getHeight());
                hash.add(Theme.getColor(Theme.key_windowBackgroundWhite));
                hash.add(Theme.getColor(Theme.key_windowBackgroundGray));
            }
            public void renderNodeUpdateDisplayList(android.graphics.Canvas canvas){
                canvas.drawColor(Theme.getColor(Theme.key_windowBackgroundWhite));
                samplePaint.setColor(Theme.getColor(Theme.key_windowBackgroundGray));
                int step=AndroidUtilities.dp(22);
                for(int x=0;x<getWidth();x+=step*2)canvas.drawRect(x,0,x+step,getHeight(),samplePaint);
            }
        });
        var factory=new org.telegram.ui.Components.blur3.BlurredBackgroundDrawableViewFactory(source);
        factory.setSourceRootView(new org.telegram.ui.Components.chat.ViewPositionWatcher(this),this);
        factory.setLiquidGlassEffectAllowed(org.telegram.messenger.LiteMode.isEnabled(org.telegram.messenger.LiteMode.FLAG_LIQUID_GLASS));
        nativeSurface=factory.create(bar,org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl.mainTabs(null));
        nativeSurface.setPadding(0);bar.setBackground(nativeSurface);
        nativeLens=factory.create(bar,null);nativeLens.setRadius(AndroidUtilities.dp(28));nativeLens.setPadding(0);
        bar.setLiquidLensBackground(nativeLens);
    }
    @Override public void updateColors(){
        surface.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        if(nativeSurface!=null)nativeSurface.updateColors();
        for(var drawable:new org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable[]{nativeSurface,nativeLens}){
            if(android.os.Build.VERSION.SDK_INT>=33 && drawable instanceof org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawableRenderNode){
                ((org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawableRenderNode)drawable)
                        .setLiquidGlassEffectAllowed(org.telegram.messenger.LiteMode.isEnabled(org.telegram.messenger.LiteMode.FLAG_LIQUID_GLASS));
            }
        }
        for(GlassTabView tab:tabs)if(tab!=null)tab.updateColorsLottie();
        bar.invalidate();
    }
    private void updateSelection(){for(int i=0;i<tabs.length;i++)tabs[i].setSelected(i==selected,true);bar.invalidate();}
    public void settingsChanged(){
        int available=getWidth()>0?getWidth():AndroidUtilities.displaySize.x-AndroidUtilities.dp(40);
        int[] shown=LiquidNavigationDestinations.fit(LiquidNavigationConfig.order(),Math.max(2,(available-AndroidUtilities.dp(16))/AndroidUtilities.dp(48)));
        if(!LiquidNavigationDestinations.contains(shown,selected))selected=shown[0];
        for(int id=0;id<tabs.length;id++){
            bar.setViewVisible(tabs[id],LiquidNavigationDestinations.contains(shown,id),false);
            tabs[id].setMainTabsAppearance(!LiquidNavigationConfig.labels()||shown.length>=6,LiquidNavigationConfig.iconDp());
        }
        if(!java.util.Arrays.equals(shown,lastShown)){
            for(int i=0;i<shown.length;i++){
                bar.setPriority(tabs[shown[i]],org.telegram.messenger.LocaleController.isRTL ? -i : i);
                tabs[shown[i]].bringToFront();
            }
            lastShown=shown;
        }
        surface.setCornerRadius(AndroidUtilities.dp(LiquidNavigationConfig.heightDp()/2f));
        if(nativeSurface!=null)nativeSurface.setRadius(AndroidUtilities.dp(LiquidNavigationConfig.heightDp()/2f));
        bar.refreshLiquidAppearance();
        android.view.ViewGroup.LayoutParams lp=bar.getLayoutParams();int height=AndroidUtilities.dp(LiquidNavigationConfig.heightDp()+16);if(lp.height!=height){lp.height=height;bar.setLayoutParams(lp);}
        updateSelection();requestLayout();invalidate();
    }
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);if(w!=oldw){removeCallbacks(afterSize);post(afterSize);}}
    @Override protected void onDetachedFromWindow(){removeCallbacks(afterSize);super.onDetachedFromWindow();}
    @Override protected void onMeasure(int w,int h){super.onMeasure(w,MeasureSpec.makeMeasureSpec(AndroidUtilities.dp(LiquidNavigationConfig.heightDp()+44),MeasureSpec.EXACTLY));}
}
