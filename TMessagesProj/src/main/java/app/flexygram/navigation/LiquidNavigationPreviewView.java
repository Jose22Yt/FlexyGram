/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;
import android.content.Context;
import android.widget.FrameLayout;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;

import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.glass.GlassTabView;
import org.telegram.ui.MainTabsLayout;

/** The real native bar, views and gesture implementation; preview clicks only change selection. */
public final class LiquidNavigationPreviewView extends FrameLayout implements Theme.Colorable {
    private final MainTabsLayout bar;
    private final GlassTabView[] tabs=new GlassTabView[10];
    private int selected;
    private int[] lastShown=new int[0];
    private final Runnable afterSize=()->{if(isAttachedToWindow())settingsChanged();};
    public void motionSettingsChanged(){bar.invalidate();}
    public LiquidNavigationPreviewView(Context context){
        super(context);setWillNotDraw(false);setMinimumHeight(AndroidUtilities.dp(354));
        bar=new MainTabsLayout(context,null);bar.refreshBottomBarAppearance();
        app.exteraless.appearance.MainTabsUiHelper.applyTabsLayoutStyle(bar,0);
        addView(bar,LayoutHelper.createFrame(-1,92,android.view.Gravity.BOTTOM|android.view.Gravity.CENTER_HORIZONTAL,8,0,8,12));
        for(int id=0;id<tabs.length;id++){
            tabs[id]=LiquidNavigationTabs.createPreview(context,id);
            final int chosen=id;tabs[id].setOnClickListener(v->{selected=chosen;updateSelection();});
            bar.addView(tabs[id]);bar.addTabToIgnoreClick(tabs[id]);
        }
        settingsChanged();
    }
    @Override public void updateColors(){
        for(GlassTabView tab:tabs)if(tab!=null)tab.updateColorsLottie();
        bar.refreshBottomBarAppearance();invalidate();
    }
    private void updateSelection(){for(int i=0;i<tabs.length;i++)tabs[i].setSelected(i==selected,true);bar.revealSelectedDestination();bar.invalidate();}
    public void settingsChanged(){
        int available=getWidth()>0?getWidth():AndroidUtilities.displaySize.x-AndroidUtilities.dp(40);
        int[] shown=LiquidNavigationConfig.shown(Math.max(2,(available-AndroidUtilities.dp(2*(LiquidNavigationConfig.sideGapDp()+LiquidNavigationConfig.innerMarginDp())))/AndroidUtilities.dp(48)));
        if(!LiquidNavigationDestinations.contains(shown,selected))selected=shown[0];
        for(int id=0;id<tabs.length;id++){
            bar.setViewVisible(tabs[id],LiquidNavigationDestinations.contains(shown,id),false);
            tabs[id].setMainTabsAppearance(LiquidNavigationConfig.hideLabels(shown.length,(int)(available/AndroidUtilities.density)),LiquidNavigationConfig.iconDp());
        }
        if(!java.util.Arrays.equals(shown,lastShown)){
            for(int i=0;i<shown.length;i++){
                bar.setPriority(tabs[shown[i]],org.telegram.messenger.LocaleController.isRTL ? -i : i);
                tabs[shown[i]].bringToFront();
            }
            lastShown=shown;
        }
        bar.refreshBottomBarAppearance();
        android.widget.FrameLayout.LayoutParams lp=(android.widget.FrameLayout.LayoutParams)bar.getLayoutParams();int height=AndroidUtilities.dp(LiquidNavigationConfig.heightDp());int side=AndroidUtilities.dp(LiquidNavigationConfig.sideGapDp()),bottom=AndroidUtilities.dp(LiquidNavigationConfig.bottomGapDp());if(lp.height!=height||lp.leftMargin!=side||lp.bottomMargin!=bottom){lp.height=height;lp.setMargins(side,0,side,bottom);bar.setLayoutParams(lp);}
        updateSelection();requestLayout();invalidate();
    }
    private final android.graphics.Paint scenePaint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    private void text(android.graphics.Canvas c,String text,float x,float y,float size,int color){scenePaint.setStyle(android.graphics.Paint.Style.FILL);scenePaint.setTextSize(AndroidUtilities.dp(size));scenePaint.setColor(color);c.drawText(text,AndroidUtilities.dp(x),AndroidUtilities.dp(y),scenePaint);}
    private void drawScene(android.graphics.Canvas c){
        int background=Theme.getColor(Theme.key_windowBackgroundWhite),ink=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText),secondary=Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2),accent=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        c.drawColor(background);float w=getWidth()/AndroidUtilities.density;
        text(c,"FlexyGram",18,32,19,ink);text(c,"⌕",w-60,32,23,secondary);text(c,"⋮",w-28,32,23,secondary);
        text(c,org.telegram.messenger.LocaleController.getString(org.telegram.messenger.R.string.MainTabsChats)+"   ·   "+org.telegram.messenger.LocaleController.getString(org.telegram.messenger.R.string.FlexyLiquidNavGroups)+"   ·   "+org.telegram.messenger.LocaleController.getString(org.telegram.messenger.R.string.FlexyLiquidNavChannels),18,62,12,accent);
        String[] names={"Design team","Alex","Weekend plans","FlexyGram News"};
        String[] lines={"Signature preview","See you tomorrow","Photo · 2","Flexy Bottom Bar"};
        for(int i=0;i<4;i++){
            float y=88+i*56;scenePaint.setColor((accent&0xffffff)|0x33000000);c.drawCircle(AndroidUtilities.dp(35),AndroidUtilities.dp(y+12),AndroidUtilities.dp(18),scenePaint);
            text(c,names[i].substring(0,1),29,y+17,15,accent);text(c,names[i],65,y+7,14,ink);text(c,lines[i],65,y+26,12,secondary);
            scenePaint.setColor((secondary&0xffffff)|0x22000000);c.drawLine(AndroidUtilities.dp(65),AndroidUtilities.dp(y+38),getWidth()-AndroidUtilities.dp(16),AndroidUtilities.dp(y+38),scenePaint);
        }
    }
    @Override protected void onDraw(android.graphics.Canvas canvas){super.onDraw(canvas);drawScene(canvas);}
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);if(w!=oldw){removeCallbacks(afterSize);post(afterSize);}}
    @Override protected void onDetachedFromWindow(){removeCallbacks(afterSize);super.onDetachedFromWindow();}
    @Override protected void onMeasure(int w,int h){super.onMeasure(w,MeasureSpec.makeMeasureSpec(AndroidUtilities.dp(LiquidNavigationConfig.heightDp()+344),MeasureSpec.EXACTLY));}
}
