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
    private android.graphics.drawable.GradientDrawable cardFill, cardMask;
    private android.graphics.drawable.RippleDrawable cardRipple;
    private android.graphics.drawable.InsetDrawable cardBackground;
    private final float[] cardCorners = new float[8];
    private float appliedTop = -1, appliedBottom = -1;
    private int appliedGap = -1;
    private int iconResource = Integer.MIN_VALUE;
    private android.content.res.Resources iconResources;
    private android.content.res.Configuration iconConfiguration;

    public void setCardEdges(boolean first, boolean last) {
        if (!card) { card = true; requestLayout(); }
        setTag(org.telegram.ui.Components.RecyclerListView.TAG_NOT_SECTION);
        this.first = first;
        this.last = last;
        updateCard();
    }

    private void updateCard() {
        pageColor = Theme.getColor(Theme.key_windowBackgroundGray, provider);
        int surface = SettingsCardStyle.surface(Theme.getColor(Theme.key_windowBackgroundWhite, provider), pageColor);
        int selector = Theme.getColor(Theme.key_listSelector, provider);
        boolean created = cardFill == null;
        if (created) {
            cardFill = new android.graphics.drawable.GradientDrawable();
            cardMask = new android.graphics.drawable.GradientDrawable();
            cardMask.setColor(0xffffffff);
            cardRipple = new android.graphics.drawable.RippleDrawable(
                    android.content.res.ColorStateList.valueOf(selector), cardFill, cardMask);
        }
        if (created || cardColor != surface) {
            cardColor = surface;
            cardFill.setColor(surface);
        }
        if (created || selectorColor != selector) {
            selectorColor = selector;
            cardRipple.setColor(android.content.res.ColorStateList.valueOf(selector));
        }
        float top = dp(first ? SettingsCardStyle.OUTER_RADIUS : SettingsCardStyle.INNER_RADIUS);
        float bottom = dp(last ? SettingsCardStyle.OUTER_RADIUS : SettingsCardStyle.INNER_RADIUS);
        if (top != appliedTop || bottom != appliedBottom) {
            appliedTop = top; appliedBottom = bottom;
            for (int i = 0; i < 4; i++) cardCorners[i] = top;
            for (int i = 4; i < 8; i++) cardCorners[i] = bottom;
            cardFill.setCornerRadii(cardCorners);
            cardMask.setCornerRadii(cardCorners);
        }
        int gap = dp(4);
        if (cardBackground == null || appliedGap != gap) {
            appliedGap = gap;
            cardBackground = new android.graphics.drawable.InsetDrawable(cardRipple, 0, 0, 0, gap);
        }
        if (getBackground() != cardBackground) setBackground(cardBackground);
    }

    private void bindIcon(int resource) {
        android.content.res.Resources resources = getResources();
        android.content.res.Configuration configuration = resources.getConfiguration();
        if (iconResource == resource && iconResources == resources
                && configuration.equals(iconConfiguration)) return;
        icon.setImageDrawable(SettingsCategoryIcon.create(getContext(), resource));
        iconResource = resource;
        iconResources = resources;
        iconConfiguration = new android.content.res.Configuration(configuration);
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
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);icon.setPadding(0,0,0,0);
        addView(icon); icon.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(title); title.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(description); description.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        setMinimumHeight(dp(compact?56:72));
    }
    private int dp(float x){return AndroidUtilities.dp(x);}
    public void bind(String name,String detail,int resource,int color,boolean divide){
        title.setText(name);description.setText(detail);description.setVisibility(compact||detail==null||detail.isEmpty()?GONE:VISIBLE);
        bindIcon(app.exteraless.settings.utils.SettingsIcons.resolve(getContext(), resource));
        icon.setBackground(null);foregroundInitialized=false;updateForeground();
        divider=divide;
        setContentDescription(name+(detail==null||detail.isEmpty()?"":", "+detail));invalidate();
    }
    @Override protected void onMeasure(int w,int h){
        int width=MeasureSpec.getSize(w),space=Math.max(0,width-dp(88));
        title.measure(MeasureSpec.makeMeasureSpec(space,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        if (description.getVisibility() != GONE) {
            description.measure(MeasureSpec.makeMeasureSpec(space,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            bodyHeight = title.getMeasuredHeight() + dp(3) + description.getMeasuredHeight();
        } else {
            bodyHeight = title.getMeasuredHeight();
        }
        icon.measure(MeasureSpec.makeMeasureSpec(dp(SettingsCardStyle.ICON),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(SettingsCardStyle.ICON),MeasureSpec.EXACTLY));
        setMeasuredDimension(width,Math.max(dp(compact?56:72),bodyHeight+dp(compact?20:24))+(card?dp(4):divider?1:0));
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        int w=getMeasuredWidth(),h=getMeasuredHeight()-(card?dp(4):0),size=dp(SettingsCardStyle.ICON);
        int ix=LocaleController.isRTL?w-dp(16)-size:dp(16),tx=LocaleController.isRTL?dp(16):dp(72),y=(h-bodyHeight)/2;
        icon.layout(ix,(h-size)/2,ix+size,(h+size)/2);
        title.layout(tx,y,tx+title.getMeasuredWidth(),y+title.getMeasuredHeight());y+=title.getMeasuredHeight()+dp(3);
        description.layout(tx,y,tx+description.getMeasuredWidth(),y+description.getMeasuredHeight());
    }
    @Override protected void dispatchDraw(Canvas c){
        updateForeground();
        if(card&&(cardColor!=SettingsCardStyle.surface(Theme.getColor(Theme.key_windowBackgroundWhite,provider),Theme.getColor(Theme.key_windowBackgroundGray,provider))||selectorColor!=Theme.getColor(Theme.key_listSelector,provider)))updateCard();
        super.dispatchDraw(c);
    }
    private int lastIconColor, lastDescriptionColor;
    private boolean foregroundInitialized;
    private void updateForeground() {
        int foreground = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, provider);
        int secondary = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2, provider);
        if (!foregroundInitialized || lastIconColor != foreground) {
            title.setTextColor(foreground);
            icon.setColorFilter(foreground);
            lastIconColor = foreground;
        }
        if (!foregroundInitialized || lastDescriptionColor != secondary) {
            description.setTextColor(secondary);
            lastDescriptionColor = secondary;
        }
        foregroundInitialized = true;
    }
    @Override protected void onDraw(Canvas c){super.onDraw(c);}
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.Button");}
}
