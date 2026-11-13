/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import app.flexygram.bubbles.BubblePreviewView;
import app.flexygram.header.HeaderPreviewView;

/** One wallpaper owner, two real bubbles and the currently selected conversation control. */
final class ConversationPreviewStage extends ViewGroup {
    private final BubblePreviewView conversation;
    private final View control;
    private final boolean header;
    ConversationPreviewStage(Context context, View control, boolean header) {
        super(context);this.control=control;this.header=header;
        conversation=new BubblePreviewView(context);addView(conversation);addView(control);
        control.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
    }
    void settingsChanged() {
        if(control instanceof HeaderPreviewView)((HeaderPreviewView)control).settingsChanged();
        control.invalidate();conversation.settingsChanged();requestLayout();
    }
    @Override protected void onMeasure(int widthSpec,int heightSpec) {
        int width=MeasureSpec.getSize(widthSpec);
        control.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        int controlHeight=control.getMeasuredHeight();
        conversation.setContentInsets(header?controlHeight:0,header?0:controlHeight);
        conversation.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        setMeasuredDimension(width,conversation.getMeasuredHeight());
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b) {
        conversation.layout(0,0,getWidth(),getHeight());
        int top=header?0:getHeight()-control.getMeasuredHeight();
        control.layout(0,top,getWidth(),top+control.getMeasuredHeight());
    }
}
