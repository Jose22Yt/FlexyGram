/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.deletion;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.RectF;
import android.os.Looper;
import android.view.Choreographer;
import android.view.View;
import android.view.ViewGroup;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;
import java.util.WeakHashMap;

/** Native snapshot lifecycle. Rendering is attributed separately in BubbleFractureRenderer. */
public final class DeleteMotionOverlay extends View implements Choreographer.FrameCallback {
    private static final int MAX_ACTIVE = 8, MAX_PIXELS = 450_000, TOTAL_PIXELS = 2_200_000;
    private static final WeakHashMap<View,DeleteMotionOverlay> running = new WeakHashMap<>();
    private static final ArrayList<DeleteMotionOverlay> live = new ArrayList<>();
    private static int active, pixels;
    private final ViewGroup host;
    private final WeakReference<View> source;
    private final float left,top,contentWidth,contentHeight;
    private final long durationMs = 2000L;
    private final int imagePixels;
    private Bitmap image;
    private BubbleFractureRenderer renderer;
    private Completion completion;
    private long firstFrame = -1;
    private float progress;
    private boolean stopped,counted,budgeted;
    private final View.OnAttachStateChangeListener hostListener = new View.OnAttachStateChangeListener() {
        public void onViewAttachedToWindow(View view) {}
        public void onViewDetachedFromWindow(View view) { stop(); }
    };
    public static final class Target {
        public final View cell;
        public final RectF localBubbleBounds;
        public Target(View cell,RectF bounds) {this.cell=cell;localBubbleBounds=new RectF(bounds);}
    }
    private static final class Completion {
        int pending;
        boolean armed,delivered;
        final Runnable callback;
        Completion(Runnable callback){this.callback=callback;}
        void finishOne(){pending--;deliver();}
        void deliver(){if(armed && pending==0 && !delivered){delivered=true;if(callback!=null)callback.run();}}
    }
    public static int runNativeDelete(ViewGroup host,List<Target> targets,int style,Runnable nativeDelete) {
        return runNativeDelete(host,targets,style,nativeDelete,null);
    }
    /** Deletion is immediate and exactly once. visualFinished owns only native holder completion. */
    public static int runNativeDelete(ViewGroup host,List<Target> targets,int style,Runnable nativeDelete,Runnable visualFinished) {
        if(nativeDelete==null)throw new IllegalArgumentException("nativeDelete required");
        if(Looper.myLooper()!=Looper.getMainLooper()){nativeDelete.run();return 0;}
        Completion completion=new Completion(visualFinished);
        ArrayList<DeleteMotionOverlay> started=new ArrayList<>();
        int chosen=DeleteMotionSettings.sanitize(style);
        if(host!=null && chosen!=0 && DeleteMotionSettings.effectsAllowed() && host.isAttachedToWindow() && targets!=null){
            for(Target target:targets){
                if(target!=null)cancel(target.cell);
                if(active>=MAX_ACTIVE)break;
                DeleteMotionOverlay overlay=capture(host,target,chosen);
                if(overlay==null)continue;
                overlay.completion=completion;completion.pending++;
                try{
                    overlay.layout(0,0,host.getWidth(),host.getHeight());
                    host.getOverlay().add(overlay);active++;overlay.counted=true;live.add(overlay);
                    running.put(target.cell,overlay);overlay.start();started.add(overlay);
                }catch(RuntimeException|OutOfMemoryError error){overlay.stop();}
            }
        }
        try{nativeDelete.run();}
        catch(RuntimeException|Error error){for(DeleteMotionOverlay overlay:started)overlay.stop();throw error;}
        completion.armed=!started.isEmpty();completion.deliver();
        return started.size();
    }
    public static void cancel(View source){DeleteMotionOverlay overlay=running.get(source);if(overlay!=null)overlay.stop();}
    public static void cancelAll(ViewGroup host){
        for(DeleteMotionOverlay overlay:new ArrayList<>(live))if(overlay.host==host)overlay.stop();
    }
    private static DeleteMotionOverlay capture(ViewGroup host,Target target,int style){
        if(target==null || target.cell==null || !target.cell.isAttachedToWindow())return null;
        RectF bounds=target.localBubbleBounds;
        if(bounds.width()<2 || bounds.height()<2 || host.getWidth()<1 || host.getHeight()<1)return null;
        int[] at=new int[2],origin=new int[2];target.cell.getLocationInWindow(at);host.getLocationInWindow(origin);
        float x=at[0]-origin[0]+bounds.left,y=at[1]-origin[1]+bounds.top;
        if(x+bounds.width()<0 || y+bounds.height()<0 || x>host.getWidth() || y>host.getHeight())return null;
        float scale=Math.min(1,(float)Math.sqrt(MAX_PIXELS/(double)(bounds.width()*bounds.height())));
        int width=Math.max(1,(int)Math.ceil(bounds.width()*scale)),height=Math.max(1,(int)Math.ceil(bounds.height()*scale));
        if(pixels+(long)width*height>TOTAL_PIXELS)return null;
        Bitmap image=null;
        org.telegram.ui.Cells.ChatMessageCell cell=target.cell instanceof org.telegram.ui.Cells.ChatMessageCell?(org.telegram.ui.Cells.ChatMessageCell)target.cell:null;
        boolean drawing=cell!=null && cell.drawingToBitmap;
        try{
            image=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);
            Canvas canvas=new Canvas(image);canvas.scale(width/bounds.width(),height/bounds.height());canvas.translate(-bounds.left,-bounds.top);
            if(cell!=null){
                cell.drawingToBitmap=true;
                if(cell.drawBackgroundInParent()){
                    int save=canvas.save();canvas.translate(0,cell.getPaddingTop());cell.drawBackgroundInternal(canvas,true);canvas.restoreToCount(save);
                }
            }
            target.cell.draw(canvas);
            DeleteMotionOverlay overlay=new DeleteMotionOverlay(host,target.cell,image,x,y,bounds.width(),bounds.height(),style);
            pixels+=width*height;overlay.budgeted=true;return overlay;
        }catch(OutOfMemoryError|RuntimeException error){if(image!=null && !image.isRecycled())image.recycle();return null;}
        finally{if(cell!=null)cell.drawingToBitmap=drawing;}
    }
    private DeleteMotionOverlay(ViewGroup host,View source,Bitmap image,float left,float top,float width,float height,int style){
        super(host.getContext());this.host=host;this.source=new WeakReference<>(source);this.image=image;
        this.left=left;this.top=top;contentWidth=width;contentHeight=height;imagePixels=image.getWidth()*image.getHeight();
        renderer=new BubbleFractureRenderer(image,width,height,getResources().getDisplayMetrics().density,style,(int)durationMs,System.nanoTime());
        setWillNotDraw(false);setClickable(false);setFocusable(false);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
    }
    private void start(){host.addOnAttachStateChangeListener(hostListener);Choreographer.getInstance().postFrameCallback(this);invalidate();}
    @Override public void doFrame(long nanos){
        if(stopped)return;
        if(firstFrame<0)firstFrame=nanos;
        progress=DeleteMotionMath.clamp((nanos-firstFrame)/(durationMs*1_000_000f));invalidate();
        if(progress>=1)stop();else Choreographer.getInstance().postFrameCallback(this);
    }
    @Override protected void onDraw(Canvas canvas){
        if(stopped || image==null || image.isRecycled())return;
        int save=canvas.save();canvas.clipRect(0,0,host.getWidth(),host.getHeight());canvas.translate(left,top);
        renderer.draw(canvas,progress,FractureMotionMath.exitDistance(top,host.getHeight(),contentWidth,contentHeight));
        canvas.restoreToCount(save);
    }
    private void stop(){
        if(stopped)return;stopped=true;
        host.removeOnAttachStateChangeListener(hostListener);Choreographer.getInstance().removeFrameCallback(this);
        View view=source.get();if(view!=null && running.get(view)==this)running.remove(view);source.clear();running.values().remove(this);
        live.remove(this);
        if(counted){counted=false;active=Math.max(0,active-1);host.getOverlay().remove(this);}
        if(budgeted){budgeted=false;pixels=Math.max(0,pixels-imagePixels);}
        // Published bitmaps can still be referenced by RenderThread; retire them through GC.
        renderer=null;image=null;
        Completion done=completion;completion=null;if(done!=null)done.finishOne();
    }
    @Override protected void onDetachedFromWindow(){stop();super.onDetachedFromWindow();}
}
