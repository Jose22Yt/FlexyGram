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
    private final ImageView icon,arrow;
    private final Theme.ResourcesProvider provider;
    private boolean divider;
    private int bodyHeight;
    private final boolean compact;
    public Settings2Cell(Context c,Theme.ResourcesProvider p){
        this(c,p,false);
    }
    public Settings2Cell(Context c,Theme.ResourcesProvider p,boolean compact){
        super(c);provider=p;this.compact=compact;setWillNotDraw(false);setFocusable(true);
        title=new TextView(c);description=new TextView(c);icon=new ImageView(c);arrow=new ImageView(c);
        title.setTextSize(compact?16:18);title.setTypeface(AndroidUtilities.bold());description.setTextSize(14);
        if(compact)title.setIncludeFontPadding(false);
        title.setGravity(Gravity.START);description.setGravity(Gravity.START);
        title.setSingleLine(false);description.setSingleLine(false);
        icon.setScaleType(ImageView.ScaleType.CENTER_INSIDE);icon.setPadding(0,0,0,0);
        arrow.setImageResource(R.drawable.round_keyboard_arrow_right_24);
        addView(icon); icon.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(title); title.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(description); description.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(arrow); arrow.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        setMinimumHeight(dp(compact?48:72));
    }
    private int dp(float x){return AndroidUtilities.dp(x);}
    public void bind(String name,String detail,int resource,int color,boolean divide){
        title.setText(name);description.setText(detail);description.setVisibility(compact||detail==null||detail.isEmpty()?GONE:VISIBLE);
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));
        description.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2,provider));
        arrow.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteGrayIcon,provider));arrow.setScaleX(LocaleController.isRTL?-1:1);
        icon.setImageResource(app.exteraless.settings.utils.SettingsIcons.resolve(getContext(), resource));icon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));
        icon.setBackground(null);lastIconColor=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        divider=divide;
        setContentDescription(name+(detail==null||detail.isEmpty()?"":", "+detail));invalidate();
    }
    @Override protected void onMeasure(int w,int h){
        int width=MeasureSpec.getSize(w),space=Math.max(0,width-dp(compact?96:108));
        title.measure(MeasureSpec.makeMeasureSpec(space,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        if (description.getVisibility() != GONE) {
            description.measure(MeasureSpec.makeMeasureSpec(space,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            bodyHeight = title.getMeasuredHeight() + dp(3) + description.getMeasuredHeight();
        } else {
            bodyHeight = title.getMeasuredHeight();
        }
        icon.measure(MeasureSpec.makeMeasureSpec(dp(24),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(24),MeasureSpec.EXACTLY));
        arrow.measure(MeasureSpec.makeMeasureSpec(dp(20),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(20),MeasureSpec.EXACTLY));
        setMeasuredDimension(width,Math.max(dp(compact?48:72),bodyHeight+dp(compact?20:24))+(divider?1:0));
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        int w=getMeasuredWidth(),h=getMeasuredHeight(),iconInset=dp(compact?8:16),textInset=dp(compact?56:68);
        int ix=LocaleController.isRTL?w-iconInset-dp(40):iconInset,tx=LocaleController.isRTL?dp(40):textInset,ax=LocaleController.isRTL?dp(compact?12:16):w-dp(compact?32:36),y=(h-bodyHeight)/2;
        icon.layout(ix+dp(8),(h-dp(24))/2,ix+dp(32),(h+dp(24))/2);
        arrow.layout(ax,(h-dp(20))/2,ax+dp(20),(h+dp(20))/2);
        title.layout(tx,y,tx+title.getMeasuredWidth(),y+title.getMeasuredHeight());y+=title.getMeasuredHeight()+dp(3);
        description.layout(tx,y,tx+description.getMeasuredWidth(),y+description.getMeasuredHeight());
    }
    @Override protected void dispatchDraw(Canvas c){
        int foreground=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        if(lastIconColor!=foreground){lastIconColor=foreground;icon.setColorFilter(foreground);}
        super.dispatchDraw(c);
    }
    private int lastIconColor;
    @Override protected void onDraw(Canvas c){super.onDraw(c);int inset=dp(compact?56:68);if(divider)c.drawRect(LocaleController.isRTL?dp(16):inset,getHeight()-1,LocaleController.isRTL?getWidth()-inset:getWidth()-dp(16),getHeight(),Theme.dividerPaint);}
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.Button");}
}
