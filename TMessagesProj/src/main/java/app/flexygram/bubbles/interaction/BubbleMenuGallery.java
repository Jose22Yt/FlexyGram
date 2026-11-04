package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Small selectable previews rendered by the exact same widgets as the real message menu. */
public final class BubbleMenuGallery extends HorizontalScrollView {
    private final Theme.ResourcesProvider provider;
    private final Runnable changed;
    private final LinearLayout strip;
    private final LinearLayout[] cards = new LinearLayout[4];
    private final Runnable alignSelection=()->{int style=BubbleMenuConfig.layout(getContext());if(cards[style]!=null)scrollTo(cards[style].getLeft(),0);};
    public BubbleMenuGallery(Context context, Theme.ResourcesProvider provider, Runnable changed) {
        super(context);this.provider=provider;this.changed=changed;
        setHorizontalScrollBarEnabled(false);setClipToPadding(false);
        strip=new LinearLayout(context);strip.setOrientation(LinearLayout.HORIZONTAL);
        addView(strip,new LayoutParams(-2,-2));refresh();
    }
    private int dp(float value){return BubbleActionPanelView.dp(getContext(),value);}
    public void refresh() {
        strip.removeAllViews();
        int[] labels={R.string.FlexyMenuList,R.string.FlexyMenuGrid,R.string.FlexyMenuGroups,R.string.FlexyMenuToolbar};
        for(int style=0;style<4;style++){
            final int selectedStyle=style;
            LinearLayout card=new LinearLayout(getContext());card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(6),dp(6),dp(6),dp(6));card.setGravity(Gravity.CENTER);
            card.addView(new Miniature(getContext(),provider,style),new LinearLayout.LayoutParams(-1,dp(142)));
            TextView title=new TextView(getContext());title.setText(LocaleController.getString(labels[style]));title.setTextSize(12);title.setMaxLines(2);title.setGravity(Gravity.CENTER);
            title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));card.addView(title,new LinearLayout.LayoutParams(-1,dp(34)));
            card.setContentDescription(title.getText());card.setFocusable(true);
            card.setOnClickListener(view->{BubbleMenuConfig.layout(getContext(),selectedStyle);selection();if(changed!=null)changed.run();});
            LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(dp(152),-2);params.setMarginEnd(dp(8));strip.addView(card,params);cards[style]=card;
        }
        selection();removeCallbacks(alignSelection);post(alignSelection);
    }
    private void selection(){
        int current=BubbleMenuConfig.layout(getContext());boolean active=BubbleInteractionSettings.signaturePanel(getContext());
        for(int style=0;style<cards.length;style++){
            boolean selected=active&&current==style;cards[style].setSelected(selected);
            GradientDrawable background=new GradientDrawable();background.setColor(Theme.getColor(Theme.key_windowBackgroundGray,provider));background.setCornerRadius(dp(16));
            int color=Theme.getColor(selected?Theme.key_windowBackgroundWhiteBlueText:Theme.key_divider,provider);
            background.setStroke(dp(selected?2:1),color);cards[style].setBackground(background);
            if(android.os.Build.VERSION.SDK_INT>=30)cards[style].setStateDescription(selected?LocaleController.getString(R.string.FlexyMenuSelected):null);
            else cards[style].setContentDescription(((TextView)cards[style].getChildAt(1)).getText()+(selected?", "+LocaleController.getString(R.string.FlexyMenuSelected):""));
        }
    }
    @Override protected void onDetachedFromWindow(){removeCallbacks(alignSelection);super.onDetachedFromWindow();}
    private static final class Miniature extends View {
        private final BubbleActionPanelView panel;
        Miniature(Context context,Theme.ResourcesProvider provider,int style){
            super(context);panel=new BubbleActionPanelView(context,provider,style,BubbleMenuConfig.actions(context));
            panel.setAllowedActions(java.util.EnumSet.allOf(BubbleActionPanelView.Action.class));
            if(style==BubbleMenuConfig.LIST){GradientDrawable background=new GradientDrawable();background.setColor(Theme.getColor(Theme.key_actionBarDefaultSubmenuBackground,provider));background.setCornerRadius(BubbleActionPanelView.dp(context,20));panel.setBackground(background);}
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }
        @Override protected void onMeasure(int width,int height){
            panel.measure(MeasureSpec.makeMeasureSpec(BubbleActionPanelView.dp(getContext(),260),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            panel.layout(0,0,panel.getMeasuredWidth(),panel.getMeasuredHeight());super.onMeasure(width,height);
        }
        @Override protected void onDraw(Canvas canvas){
            super.onDraw(canvas);float factor=Math.min((getWidth()-8f)/Math.max(1,panel.getWidth()),(getHeight()-8f)/Math.max(1,panel.getHeight()));
            int save=canvas.save();canvas.translate((getWidth()-panel.getWidth()*factor)/2,(getHeight()-panel.getHeight()*factor)/2);canvas.scale(factor,factor);panel.draw(canvas);canvas.restoreToCount(save);
        }
    }
}
