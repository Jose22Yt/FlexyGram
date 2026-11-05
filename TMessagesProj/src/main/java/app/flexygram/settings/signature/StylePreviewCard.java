/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.LinearLayout;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/** A wallpaper-filled segment, exposed as one accessible radio choice. */
public final class StylePreviewCard extends LinearLayout {
    private final View preview;
    private final Theme.ResourcesProvider provider;
    private final String name;
    private final GradientDrawable frame = new GradientDrawable();
    private final Path clip = new Path();
    private final RectF clipBounds = new RectF();
    private final float[] corners = new float[8];
    private int surface, accent, divider;
    private boolean first=true,last=true;
    public StylePreviewCard(Context context, Theme.ResourcesProvider provider, String name, View preview, Runnable choose) {
        this(context,provider,name,preview,choose,false);
    }
    public StylePreviewCard(Context context, Theme.ResourcesProvider provider, String name, View preview, Runnable choose, boolean compact) {
        super(context);this.provider=provider;this.name=name;this.preview=preview;
        setOrientation(VERTICAL);setPadding(dp(2),dp(2),dp(2),dp(2));setFocusable(true);
        setBackground(frame);
        preview.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
        addView(preview,new LayoutParams(-1,-2));
        if(android.os.Build.VERSION.SDK_INT>=26)setTooltipText(name);
        setContentDescription(name);setOnClickListener(v->choose.run());
        setSegmentEdges(true,true);updateColors();
    }
    private int dp(int value){return AndroidUtilities.dp(value);}
    public void setSegmentEdges(boolean first,boolean last){
        this.first=first;this.last=last;
        float top=dp(first?28:6),bottom=dp(last?28:6);
        for(int i=0;i<4;i++)corners[i]=top;
        for(int i=4;i<8;i++)corners[i]=bottom;
        frame.setCornerRadii(corners);updateClip();invalidate();
    }
    private void updateClip(){
        clipBounds.set(dp(2),dp(2),Math.max(dp(2),getWidth()-dp(2)),Math.max(dp(2),getHeight()-dp(2)));
        float top=dp(first?26:4),bottom=dp(last?26:4);
        for(int i=0;i<4;i++)corners[i]=top;
        for(int i=4;i<8;i++)corners[i]=bottom;
        clip.rewind();clip.addRoundRect(clipBounds,corners,Path.Direction.CW);
    }
    @Override protected void onSizeChanged(int w,int h,int ow,int oh){super.onSizeChanged(w,h,ow,oh);updateClip();}
    public void bind(boolean selected){setSelected(selected);updateColors();preview.invalidate();}
    public void refreshPreview(){preview.invalidate();}
    private void updateColors(){
        surface=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
        accent=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider);
        divider=Theme.getColor(Theme.key_divider,provider);
        frame.setColor(surface);frame.setStroke(dp(isSelected()?2:1),isSelected()?accent:divider);
    }
    @Override protected void dispatchDraw(Canvas canvas){
        if(surface!=Theme.getColor(Theme.key_windowBackgroundWhite,provider)||accent!=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider)||divider!=Theme.getColor(Theme.key_divider,provider))updateColors();
        int save=canvas.save();canvas.clipPath(clip);super.dispatchDraw(canvas);canvas.restoreToCount(save);
    }
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.RadioButton");info.setContentDescription(name);info.setCheckable(true);info.setChecked(isSelected());}
}
