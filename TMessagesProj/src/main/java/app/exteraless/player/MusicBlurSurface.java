package app.exteraless.player;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewTreeObserver;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LiteMode;

/** Cropped, downsampled backdrop. Captures only on existing draws, never on a polling loop. */
final class MusicBlurSurface extends Drawable implements ViewTreeObserver.OnPreDrawListener, ViewTreeObserver.OnScrollChangedListener, ViewTreeObserver.OnGlobalLayoutListener {
    private static boolean capturing;
    private final View target;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final RectF rect = new RectF();
    private final Path clip = new Path();
    private Bitmap bitmap;
    private ViewTreeObserver observer;
    private boolean attached, pending, dirty = true;
    private final int[] position = new int[2];
    private int lastX = Integer.MIN_VALUE, lastY = Integer.MIN_VALUE;
    private int generation;
    private long lastCapture = -160;
    private int surface, outline;
    private float radius;
    private float segmentWidth, segmentGap;
    private final boolean allowGlass;
    private MusicGlassRenderer glass;

    MusicBlurSurface(View target, float radius) { this(target,radius,false); }
    MusicBlurSurface(View target,float radius,boolean allowGlass) { this.target=target;this.radius=radius;this.allowGlass=allowGlass; }
    void setSegments(float controlsWidth,float gap){if(segmentWidth!=controlsWidth||segmentGap!=gap){segmentWidth=controlsWidth;segmentGap=gap;invalidateSelf();}}
    static boolean isCapturing() { return capturing; }
    void setColors(PlayerColors colors) {
        int fill=allowGlass?colors.surfaceHigh:colors.surface;
        if (surface == fill && outline == colors.outlineVariant) return;
        surface = fill; outline = colors.outlineVariant; dirty = true;
        invalidateSelf();
    }
    void attach() {
        if (attached) return;
        attached = true; generation++; lastCapture = -160; dirty = true;
        observer = target.getViewTreeObserver(); observer.addOnPreDrawListener(this);
        observer.addOnScrollChangedListener(this); observer.addOnGlobalLayoutListener(this);
        target.invalidate();
    }
    void detach() {
        if (!attached) return;
        attached = false; generation++; pending = false;
        if (observer != null && observer.isAlive()) {
            observer.removeOnPreDrawListener(this); observer.removeOnScrollChangedListener(this); observer.removeOnGlobalLayoutListener(this);
        }
        observer = null;
        // A published bitmap may still be referenced by RenderThread. Let GC retire it safely.
        bitmap = null;if(glass!=null){glass.clear();glass=null;}
    }
    @Override public void onScrollChanged() { dirty = true; target.invalidate(); }
    @Override public void onGlobalLayout() { dirty = true; target.invalidate(); }
    @Override public boolean onPreDraw() {
        if (!attached || pending || capturing || !target.isShown() || target.getAlpha() == 0
                || target.getWidth() < 8 || target.getHeight() < 8) return true;
        if (!LiteMode.isEnabled(LiteMode.FLAG_CHAT_BLUR)) {
            dirty = true;
            if (bitmap != null) { bitmap = null;if(glass!=null){glass.clear();glass=null;} invalidateSelf(); }
            return true;
        }
        target.getLocationOnScreen(position);
        if (position[0] != lastX || position[1] != lastY) dirty = true;
        if (!dirty) return true;
        long now = SystemClock.uptimeMillis();
        if (now - lastCapture < 160) return true;
        lastCapture = now; pending = true; dirty = false;
        lastX = position[0]; lastY = position[1];
        final int ticket = generation, width = target.getWidth(), height = target.getHeight();
        capturing = true;
        try {
            AndroidUtilities.makeGlobalBlurBitmap(result -> AndroidUtilities.runOnUIThread(() -> {
                if (!attached || ticket != generation) { if (result != null) result.recycle(); return; }
                pending = false;
                if (target.getWidth() != width || target.getHeight() != height) {
                    if (result != null) result.recycle(); dirty = true; target.invalidate(); return;
                }
                bitmap = result; invalidateSelf();
            }), 8, 4, target, null, true);
        } catch (RuntimeException error) { pending = false; bitmap = null; }
        finally { capturing = false; }
        return true;
    }
    @Override public void draw(Canvas canvas) {
        rect.set(getBounds()); if (rect.isEmpty()) return;
        clip.rewind();
        float split=rect.right-segmentWidth;
        if(segmentWidth>0&&split>rect.left){
            clip.addRoundRect(rect.left,rect.top,split-segmentGap,rect.bottom,radius,radius,Path.Direction.CW);
            clip.addRoundRect(split,rect.top,rect.right,rect.bottom,radius,radius,Path.Direction.CW);
        }else clip.addRoundRect(rect, radius, radius, Path.Direction.CW);
        if(allowGlass&&android.os.Build.VERSION.SDK_INT>=33&&canvas.isHardwareAccelerated()&&bitmap!=null&&!bitmap.isRecycled()
                &&LiteMode.isEnabled(LiteMode.FLAG_LIQUID_GLASS)){
            if(glass==null)glass=new MusicGlassRenderer(target,radius);
            glass.draw(canvas,bitmap,getBounds(),surface,outline);return;
        }
        int save = canvas.save(); canvas.clipPath(clip);
        if (bitmap != null && !bitmap.isRecycled()) {
            paint.setColor(0xffffffff); canvas.drawBitmap(bitmap, null, rect, paint);
            paint.setColor((surface & 0xffffff) | (allowGlass?0x99000000:0xc9000000));
        } else paint.setColor(surface);
        canvas.drawRect(rect, paint); canvas.restoreToCount(save);
        paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(AndroidUtilities.dpf2(.7f));
        paint.setColor(outline); rect.inset(.5f,.5f); canvas.drawPath(clip,paint);
        paint.setStyle(Paint.Style.FILL);
    }
    @Override public void setAlpha(int alpha) { }
    @Override public void setColorFilter(ColorFilter filter) { }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
}
