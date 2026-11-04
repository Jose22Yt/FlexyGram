/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.content.Context;
import android.graphics.*;
import android.view.*;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.*;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.Theme;
/** Recycled native row. Layout adapts to font/RTL; no blur, bitmap or frame callback. */
public final class Settings2Cell extends FrameLayout {
    private final TextView title,description;
    private final ImageView icon;
    private final Theme.ResourcesProvider provider;
    private boolean divider;
    private int bodyHeight;
    private final boolean compact;
    private boolean card, first, last;
    private int cardColor, selectorColor, pageColor;
    public void setCardEdges(boolean first,boolean last){card=true;setTag(org.telegram.ui.Components.RecyclerListView.TAG_NOT_SECTION);this.first=first;this.last=last;updateCard();}
    private void updateCard(){
        pageColor=Theme.getColor(Theme.key_windowBackgroundGray,provider);cardColor=SettingsCardStyle.surface(Theme.getColor(Theme.key_windowBackgroundWhite,provider),pageColor);selectorColor=Theme.getColor(Theme.key_listSelector,provider);
        android.graphics.drawable.GradientDrawable fill=new android.graphics.drawable.GradientDrawable();fill.setColor(cardColor);
        float top=dp(first?SettingsCardStyle.OUTER_RADIUS:SettingsCardStyle.INNER_RADIUS),bottom=dp(last?SettingsCardStyle.OUTER_RADIUS:SettingsCardStyle.INNER_RADIUS);float[] corners={top,top,top,top,bottom,bottom,bottom,bottom};fill.setCornerRadii(corners);
        android.graphics.drawable.GradientDrawable mask=new android.graphics.drawable.GradientDrawable();mask.setColor(0xffffffff);mask.setCornerRadii(corners);
        setBackground(new android.graphics.drawable.InsetDrawable(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(selectorColor),fill,mask),0,0,0,dp(4)));
    }
    public Settings2Cell(Context c,Theme.ResourcesProvider p){
        this(c,p,true);
    }
    public Settings2Cell(Context c,Theme.ResourcesProvider p,boolean compact){
        super(c);provider=p;this.compact=compact;setWillNotDraw(false);setFocusable(true);
        title=new TextView(c);description=new TextView(c);icon=new ImageView(c);
        title.setTextSize(compact?16:18);title.setTypeface(AndroidUtilities.bold());description.setTextSize(14);
        if(compact)title.setIncludeFontPadding(false);
        title.setGravity(Gravity.START);description.setGravity(Gravity.START);
        title.setSingleLine(false);description.setSingleLine(false);
        icon.setScaleType(ImageView.ScaleType.CENTER_INSIDE);icon.setPadding(0,0,0,0);
        addView(icon); icon.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(title); title.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(description); description.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        setMinimumHeight(dp(compact?48:72));
    }
    private int dp(float x){return AndroidUtilities.dp(x);}
    public void bind(String name,String detail,int resource,int color,boolean divide){
        title.setText(name);description.setText(detail);description.setVisibility(compact||detail==null||detail.isEmpty()?GONE:VISIBLE);
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));
        description.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2,provider));
        icon.setImageDrawable(SettingsCategoryIcon.create(getContext(),app.exteraless.settings.utils.SettingsIcons.resolve(getContext(), resource)));icon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));
        icon.setBackground(null);lastIconColor=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        divider=divide;
        setContentDescription(name+(detail==null||detail.isEmpty()?"":", "+detail));invalidate();
    }
    @Override protected void onMeasure(int w,int h){
        int width=MeasureSpec.getSize(w),space=Math.max(0,width-dp(72));
        title.measure(MeasureSpec.makeMeasureSpec(space,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        if (description.getVisibility() != GONE) {
            description.measure(MeasureSpec.makeMeasureSpec(space,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            bodyHeight = title.getMeasuredHeight() + dp(3) + description.getMeasuredHeight();
        } else {
            bodyHeight = title.getMeasuredHeight();
        }
        icon.measure(MeasureSpec.makeMeasureSpec(dp(SettingsCardStyle.ICON),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(SettingsCardStyle.ICON),MeasureSpec.EXACTLY));
        setMeasuredDimension(width,Math.max(dp(compact?48:72),bodyHeight+dp(compact?20:24))+(card?dp(4):divider?1:0));
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        int w=getMeasuredWidth(),h=getMeasuredHeight()-(card?dp(4):0),size=dp(SettingsCardStyle.ICON);
        int ix=LocaleController.isRTL?w-dp(16)-size:dp(16),tx=LocaleController.isRTL?dp(16):dp(56),y=(h-bodyHeight)/2;
        icon.layout(ix,(h-size)/2,ix+size,(h+size)/2);
        title.layout(tx,y,tx+title.getMeasuredWidth(),y+title.getMeasuredHeight());y+=title.getMeasuredHeight()+dp(3);
        description.layout(tx,y,tx+description.getMeasuredWidth(),y+description.getMeasuredHeight());
    }
    @Override protected void dispatchDraw(Canvas c){
        int foreground=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        if(lastIconColor!=foreground){lastIconColor=foreground;icon.setColorFilter(foreground);}
        if(card&&(cardColor!=SettingsCardStyle.surface(Theme.getColor(Theme.key_windowBackgroundWhite,provider),Theme.getColor(Theme.key_windowBackgroundGray,provider))||selectorColor!=Theme.getColor(Theme.key_listSelector,provider)))updateCard();
        super.dispatchDraw(c);
    }
    private int lastIconColor;
    @Override protected void onDraw(Canvas c){super.onDraw(c);}
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.Button");}
}
