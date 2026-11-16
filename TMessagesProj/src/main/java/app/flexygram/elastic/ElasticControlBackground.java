package app.flexygram.elastic;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.view.View;

/** A control owns both its retained native material and its original ripple.
 * No screen capture, intermediate bitmap, per-frame allocation or input listener.
 */
public final class ElasticControlBackground extends Drawable implements Drawable.Callback {
    private final Drawable material;
    private Drawable original;
    private ElasticControlBackground(Drawable material, Drawable original) {
        this.material=material;this.original=original;
        material.setCallback(this);
        if(original!=null)original.setCallback(this);
    }
    public static void install(View control, Drawable material) {
        if(control.getBackground() instanceof ElasticControlBackground)return;
        int l=control.getPaddingLeft(),t=control.getPaddingTop(),r=control.getPaddingRight(),b=control.getPaddingBottom();
        control.setBackground(new ElasticControlBackground(material,control.getBackground()));
        control.setPadding(l,t,r,b);
        control.setTag(org.telegram.messenger.R.id.flexy_elastic_surface,control);
    }
    public static void updateOriginal(View control,Drawable original) {
        if(control.getBackground() instanceof ElasticControlBackground){
            ElasticControlBackground background=(ElasticControlBackground)control.getBackground();
            if(background.original!=null)background.original.setCallback(null);
            background.original=original;
            if(original!=null){original.setCallback(background);original.setBounds(background.getBounds());original.setState(background.getState());}
            background.invalidateSelf();
        }else control.setBackground(original);
    }
    @Override public void draw(Canvas canvas) {
        if(ElasticConfig.enabled())material.draw(canvas);
        if(original!=null)original.draw(canvas);
    }
    @Override protected void onBoundsChange(Rect bounds) {
        material.setBounds(bounds);
        if(original!=null)original.setBounds(bounds);
    }
    @Override public boolean getPadding(Rect padding) {
        if(original!=null)return original.getPadding(padding);
        padding.setEmpty();return false;
    }
    @Override public boolean setVisible(boolean visible,boolean restart){
        boolean changed=super.setVisible(visible,restart)|material.setVisible(visible,restart);
        if(original!=null)changed=original.setVisible(visible,restart)|changed;
        return changed;
    }
    @Override protected boolean onLevelChange(int level){
        boolean changed=material.setLevel(level);
        if(original!=null)changed=original.setLevel(level)|changed;
        return changed;
    }
    @Override public void getOutline(android.graphics.Outline outline){
        if(ElasticConfig.enabled())material.getOutline(outline);
        else if(original!=null)original.getOutline(outline);
        else outline.setEmpty();
    }
    @Override public int getMinimumWidth(){return original==null?0:original.getMinimumWidth();}
    @Override public int getMinimumHeight(){return original==null?0:original.getMinimumHeight();}
    @Override public boolean isStateful(){return material.isStateful()||original!=null&&original.isStateful();}
    @Override protected boolean onStateChange(int[] state){
        boolean changed=material.setState(state);
        if(original!=null)changed=original.setState(state)||changed;
        return changed;
    }
    @Override public void setHotspot(float x,float y){if(original!=null)original.setHotspot(x,y);}
    @Override public void jumpToCurrentState(){material.jumpToCurrentState();if(original!=null)original.jumpToCurrentState();}
    @Override public void setAlpha(int alpha){material.setAlpha(alpha);if(original!=null)original.setAlpha(alpha);}
    @Override public void setColorFilter(ColorFilter filter){material.setColorFilter(filter);if(original!=null)original.setColorFilter(filter);}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    @Override public void invalidateDrawable(Drawable who){invalidateSelf();}
    @Override public void scheduleDrawable(Drawable who,Runnable task,long when){scheduleSelf(task,when);}
    @Override public void unscheduleDrawable(Drawable who,Runnable task){unscheduleSelf(task);}
}
