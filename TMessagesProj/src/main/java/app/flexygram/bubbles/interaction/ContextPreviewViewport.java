/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;

/** Touch/accessibility scroll for the temporary selected-message preview only. */
public final class ContextPreviewViewport extends View {
    public interface Listener { void scrollTo(float value); }
    private float range, offset, lastY;
    private Listener listener;
    public ContextPreviewViewport(Context context) { super(context); }
    public void configure(float range, CharSequence description, Listener listener) {
        this.range=Math.max(0,range); this.listener=listener;
        setContentDescription(description); setFocusable(range>0);
        setImportantForAccessibility(range>0?IMPORTANT_FOR_ACCESSIBILITY_YES:IMPORTANT_FOR_ACCESSIBILITY_NO);
    }
    private void move(float value) {
        offset=Math.max(0,Math.min(range,value));
        if(listener!=null)listener.scrollTo(offset);
    }
    @Override public boolean onTouchEvent(MotionEvent e) {
        if(range<=0)return false;
        if(e.getActionMasked()==MotionEvent.ACTION_DOWN) {lastY=e.getY();return true;}
        if(e.getActionMasked()==MotionEvent.ACTION_MOVE) {move(offset+lastY-e.getY());lastY=e.getY();return true;}
        if(e.getActionMasked()==MotionEvent.ACTION_UP) {performClick();return true;}
        return e.getActionMasked()==MotionEvent.ACTION_CANCEL;
    }
    @Override public boolean performClick() {super.performClick();return true;}
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info) {
        super.onInitializeAccessibilityNodeInfo(info);info.setScrollable(range>0);
        if(offset<range)info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_FORWARD);
        if(offset>0)info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_BACKWARD);
    }
    @Override public boolean performAccessibilityAction(int action, Bundle args) {
        if(action==AccessibilityNodeInfo.ACTION_SCROLL_FORWARD) {move(offset+getHeight()*.8f);return true;}
        if(action==AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD) {move(offset-getHeight()*.8f);return true;}
        return super.performAccessibilityAction(action,args);
    }
}
