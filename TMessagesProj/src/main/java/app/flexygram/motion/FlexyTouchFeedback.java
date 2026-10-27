/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;
import android.graphics.Canvas;
import android.view.MotionEvent;
import android.view.View;

/** Draw-only compression: never changes layout, View scale, hit bounds, pivots or native click listeners. */
public final class FlexyTouchFeedback implements View.OnAttachStateChangeListener {
    private final View view;private final FlexyFrameMotion motion;private float factor=1,pivotX,pivotY;private boolean active;private int pointer=-1;
    public FlexyTouchFeedback(View view){this.view=view;motion=new FlexyFrameMotion(view,1,value->{factor=value;view.invalidate();});motion.setOnSettingsChanged(()->{FlexyMotionSettings.State s=FlexyMotionSettings.state(view.getContext());if(s.instant())reset();else if(active)motion.animateTo(s.pressedScale);});view.addOnAttachStateChangeListener(this);}
    public void transform(Canvas canvas){if(factor!=1)canvas.scale(factor,factor,pivotX,pivotY);}
    public float factor(){return factor;}
    public void onTouch(MotionEvent e){
        switch(e.getActionMasked()){
            case MotionEvent.ACTION_DOWN:
                if(!view.isEnabled())return;active=true;pointer=e.getPointerId(0);pivotX=Math.max(0,Math.min(view.getWidth(),e.getX()));pivotY=Math.max(0,Math.min(view.getHeight(),e.getY()));
                FlexyMotionSettings.State s=FlexyMotionSettings.state(view.getContext());motion.animateTo(s.instant()?1:s.pressedScale);break;
            case MotionEvent.ACTION_MOVE:
                int i=e.findPointerIndex(pointer);if(active&&(i<0||e.getX(i)<0||e.getY(i)<0||e.getX(i)>view.getWidth()||e.getY(i)>view.getHeight()))release();break;
            case MotionEvent.ACTION_POINTER_UP:if(e.getPointerId(e.getActionIndex())==pointer)release();break;
            case MotionEvent.ACTION_UP:case MotionEvent.ACTION_CANCEL:release();break;
        }
    }
    public void release(){if(active){active=false;pointer=-1;motion.animateTo(1);}}
    public void reset(){active=false;pointer=-1;motion.snapTo(1);}
    public void dispose(){reset();motion.dispose();view.removeOnAttachStateChangeListener(this);}
    @Override public void onViewAttachedToWindow(View v){}
    @Override public void onViewDetachedFromWindow(View v){reset();}
}
