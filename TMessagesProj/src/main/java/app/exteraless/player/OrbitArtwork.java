package app.exteraless.player;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Path;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.FrameLayout;
import org.telegram.messenger.AndroidUtilities;

/** One real artwork view and a seekable ring. No duplicate bitmap or rotating-artwork timer. */
public final class OrbitArtwork extends FrameLayout {
    private final CoverImage cover;
    private final Path circle = new Path();
    private final LuminousProgressRing luminousRing = new LuminousProgressRing();
    private float progress, ringAlpha = 1;
    private int accent, track;
    private boolean dragging;
    private WavySeekBar.Delegate delegate;
    public OrbitArtwork(Context context, CoverImage image) {
        super(context); cover=image; if(cover.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)cover.getParent()).removeView(cover);addView(cover,new LayoutParams(-1,-1));setWillNotDraw(false);
        setFocusable(true);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
    public void setDelegate(WavySeekBar.Delegate value) { delegate=value; }
    public void setProgress(float value) { if(!dragging && progress!=unit(value)){progress=unit(value);if(ringAlpha>0)invalidate();} }
    public float getProgress() { return progress; }
    public void setRingAlpha(float value) { if(ringAlpha!=value){ringAlpha=value;invalidate();} }
    public void setColors(PlayerColors colors) { accent=colors.primary;track=colors.outlineVariant;luminousRing.setColors(accent,track);invalidate(); }
    private static float unit(float value) { return Float.isFinite(value)?Math.max(0,Math.min(1,value)):0; }
    @Override protected void onSizeChanged(int w,int h,int ow,int oh) {
        super.onSizeChanged(w,h,ow,oh);circle.rewind();circle.addCircle(w*.5f,h*.5f,Math.max(0,Math.min(w,h)*.5f-AndroidUtilities.dp(14)),Path.Direction.CW);
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b) {
        int inset=AndroidUtilities.dp(14);cover.layout(inset,inset,r-l-inset,b-t-inset);cover.setRadius(Math.max(1,(r-l-inset*2)/2));
    }
    @Override protected void dispatchDraw(Canvas canvas) {
        int save=canvas.save();canvas.clipPath(circle);super.dispatchDraw(canvas);canvas.restoreToCount(save);
        luminousRing.draw(canvas,getWidth(),getHeight(),progress,ringAlpha);
    }
    private void updateFromTouch(MotionEvent event) {
        float value=(float)((Math.atan2(event.getY()-getHeight()*.5f,event.getX()-getWidth()*.5f)+Math.PI*.5)/(Math.PI*2));
        if(value<0)value+=1;
        // Cross the twelve-o'clock seam continuously rather than jumping an entire song.
        if(dragging&&Math.abs(value-progress)>.5f)value=progress>.5f?1:0;
        progress=unit(value);if(delegate!=null)delegate.onSeekMove(progress);invalidate();
    }
    @Override public boolean onTouchEvent(MotionEvent event) {
        if(!isEnabled())return false;
        switch(event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                float dx=event.getX()-getWidth()*.5f,dy=event.getY()-getHeight()*.5f;
                if(Math.abs((float)Math.hypot(dx,dy)-getWidth()*.5f)>AndroidUtilities.dp(24))return false;
                if(delegate!=null)delegate.onSeekStart();updateFromTouch(event);dragging=true;getParent().requestDisallowInterceptTouchEvent(true);return true;
            case MotionEvent.ACTION_MOVE:if(dragging){updateFromTouch(event);return true;}return false;
            case MotionEvent.ACTION_UP:if(dragging){updateFromTouch(event);dragging=false;if(delegate!=null)delegate.onSeekEnd(progress,true);getParent().requestDisallowInterceptTouchEvent(false);performClick();return true;}return false;
            case MotionEvent.ACTION_CANCEL:if(dragging){dragging=false;if(delegate!=null)delegate.onSeekEnd(progress,false);getParent().requestDisallowInterceptTouchEvent(false);return true;}return false;
        }return false;
    }
    @Override public boolean performClick(){super.performClick();return true;}
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.SeekBar");info.setRangeInfo(AccessibilityNodeInfo.RangeInfo.obtain(AccessibilityNodeInfo.RangeInfo.RANGE_TYPE_PERCENT,0,100,progress*100));info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SET_PROGRESS);info.addAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD);info.addAction(AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD);}
    @Override public boolean performAccessibilityAction(int action,Bundle args){
        float value=progress;
        if(action==AccessibilityNodeInfo.ACTION_SCROLL_FORWARD)value+=.05f;
        else if(action==AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD)value-=.05f;
        else if(action==AccessibilityNodeInfo.AccessibilityAction.ACTION_SET_PROGRESS.getId()&&args!=null)value=args.getFloat(AccessibilityNodeInfo.ACTION_ARGUMENT_PROGRESS_VALUE)/100;
        else return super.performAccessibilityAction(action,args);
        if(!isEnabled()||delegate==null)return false;delegate.onSeekStart();progress=unit(value);delegate.onSeekMove(progress);delegate.onSeekEnd(progress,true);invalidate();return true;
    }
    @Override protected void onDetachedFromWindow(){if(dragging){dragging=false;if(delegate!=null)delegate.onSeekEnd(progress,false);}super.onDetachedFromWindow();}
}
