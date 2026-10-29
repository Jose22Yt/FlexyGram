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
        settingsChanged();
    }
    @Override public void updateColors(){
        surface.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
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
        bar.refreshLiquidAppearance();
        android.view.ViewGroup.LayoutParams lp=bar.getLayoutParams();int height=AndroidUtilities.dp(LiquidNavigationConfig.heightDp()+16);if(lp.height!=height){lp.height=height;bar.setLayoutParams(lp);}
        updateSelection();requestLayout();invalidate();
    }
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);if(w!=oldw){removeCallbacks(afterSize);post(afterSize);}}
    @Override protected void onDetachedFromWindow(){removeCallbacks(afterSize);super.onDetachedFromWindow();}
    @Override protected void onMeasure(int w,int h){super.onMeasure(w,MeasureSpec.makeMeasureSpec(AndroidUtilities.dp(LiquidNavigationConfig.heightDp()+44),MeasureSpec.EXACTLY));}
}
