package app.flexygram.icons;

import android.animation.ValueAnimator;
import android.graphics.Matrix;
import android.graphics.Rect;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.view.*;
import android.widget.ImageView;
import android.widget.TextView;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import app.flexygram.animation.FastMotionTiming;

/** Observes confirmed taps; never consumes, delays or synthesizes a native action.
 * One finite frame callback for the current touch. No DOWN/MOVE animation while scrolling. */
public final class IconPressFeedback {
    public interface Target { void setIconPressScale(float scale); }
    private static final Rect hit = new Rect();
    private static float downX, downY;
    private static boolean candidate;
    private static int slop;
    private static Pulse active;
    private static MotionEvent lastEvent;
    private static long lastTime;
    private static int lastAction;
    private IconPressFeedback() {}
    public static void observe(View root, MotionEvent event) {
        // Disabled: icon touch pulse animation causes errors and visual glitches. Icons remain static and fluid.
        return;
    }
    private static View find(View view,float x,float y) {
        if(view.getVisibility()!=View.VISIBLE || !view.isEnabled() || view.getAlpha()==0
                || !view.getGlobalVisibleRect(hit) || !hit.contains((int)x,(int)y))return null;
        if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;
            for(int i=group.getChildCount()-1;i>=0;i--){View found=find(group.getChildAt(i),x,y);if(found!=null)return found;}}
        return view.isClickable() || view instanceof Target || view instanceof ImageView
                || view instanceof TextView || view.getParent() instanceof View && isList((View)view.getParent()) ? view : null;
    }
    private static boolean isList(View view){
        if(view==null)return false;
        if(view instanceof android.widget.AbsListView)return true;
        for(Class<?> type=view.getClass();type!=null;type=type.getSuperclass())
            if(type.getName().equals("androidx.recyclerview.widget.RecyclerView"))return true;
        return false;
    }
    private static void collect(View view,ArrayList<Item> items,boolean root) {
        if(items.size()>=4 || view.getVisibility()!=View.VISIBLE || !view.isEnabled())return;
        if(!root && view.isClickable())return;
        if(view instanceof Target){items.add(new Item(view));return;}
        if(view instanceof ImageView){
            ImageView image=(ImageView)view;Drawable drawable=image.getDrawable();
            float limit=96*view.getResources().getDisplayMetrics().density;
            if(drawable!=null && !(drawable instanceof BitmapDrawable) && image.getWidth()<=limit && image.getHeight()<=limit){
                if(drawable instanceof Target)items.add(new Item(image,(Target)drawable));
                else items.add(new Item(image));
            }
        } else if(view instanceof TextView){
            Drawable[] compounds=((TextView)view).getCompoundDrawablesRelative();
            for(int i=0;i<compounds.length;i++)if(compounds[i] instanceof CupertinoGlyphDrawable)
                items.add(new CompoundItem(view,compounds[i]));
        } else if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;
            for(int i=0;i<group.getChildCount();i++)collect(group.getChildAt(i),items,false);}
    }
    private static class Item {
        final WeakReference<View> owner;
        final Drawable drawable;
        final Target target;
        final ImageView.ScaleType scaleType;
        final Matrix original, matrix;
        Item(View view){this(view,view instanceof Target?(Target)view:null);}
        Item(View view,Target target){
            owner=new WeakReference<>(view);this.target=target;
            if(view instanceof ImageView && target==null){ImageView image=(ImageView)view;
                drawable=image.getDrawable();scaleType=image.getScaleType();original=new Matrix(image.getImageMatrix());matrix=new Matrix();
                image.setScaleType(ImageView.ScaleType.MATRIX);
            } else {drawable=view instanceof ImageView?((ImageView)view).getDrawable():null;scaleType=null;original=matrix=null;}
        }
        boolean apply(float scale){
            View view=owner.get();if(view==null)return false;
            if(!view.isAttachedToWindow() || view instanceof ImageView && ((ImageView)view).getDrawable()!=drawable){reset();return false;}
            if(target!=null)target.setIconPressScale(scale);
            else {ImageView image=(ImageView)view;matrix.set(original);
                matrix.postScale(scale,scale,(image.getWidth()-image.getPaddingLeft()-image.getPaddingRight())/2f,
                        (image.getHeight()-image.getPaddingTop()-image.getPaddingBottom())/2f);image.setImageMatrix(matrix);}
            return true;
        }
        void reset(){View view=owner.get();if(view==null)return;
            if(target!=null)target.setIconPressScale(1);
            else {ImageView image=(ImageView)view;
                if(image.getScaleType()==ImageView.ScaleType.MATRIX){
                    if(image.getDrawable()==drawable)image.setImageMatrix(original);
                    image.setScaleType(scaleType);
                }}
        }
    }
    private static final class CompoundItem extends Item {
        final CupertinoGlyphDrawable symbol;
        CompoundItem(View view,Drawable symbol){super(view);this.symbol=(CupertinoGlyphDrawable)symbol;}
        @Override boolean apply(float scale){
            View view=owner.get();if(view==null||!view.isAttachedToWindow()||symbol.getCallback()!=view){reset();return false;}
            symbol.setPressScale(scale);return true;
        }
        @Override void reset(){symbol.setPressScale(1);}
    }
    private static final class Pulse implements Choreographer.FrameCallback {
        final ArrayList<Item> items;final boolean reduced;long start;
        Pulse(ArrayList<Item> items,boolean reduced){this.items=items;this.reduced=reduced;}
        void start(){Choreographer.getInstance().postFrameCallback(this);}
        @Override public void doFrame(long nanos){
            if(start==0)start=nanos;
            float progress=(nanos-start)/(IconPressCurve.duration(reduced)*1000000f);
            if(progress>=1){finish();return;}
            boolean alive=false;float scale=IconPressCurve.scale(progress,reduced);
            for(int i=0;i<items.size();i++)alive|=items.get(i).apply(scale);
            if(alive)Choreographer.getInstance().postFrameCallback(this);else finish();
        }
        void finish(){Choreographer.getInstance().removeFrameCallback(this);
            for(int i=0;i<items.size();i++)items.get(i).reset();if(active==this)active=null;}
    }
}
