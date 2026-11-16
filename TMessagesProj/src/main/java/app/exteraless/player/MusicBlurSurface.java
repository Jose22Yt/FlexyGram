package app.exteraless.player;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.Rect;
import android.graphics.Matrix;
import android.graphics.drawable.Drawable;
import android.view.View;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LiteMode;

/** Cropped, downsampled backdrop. Captures only on existing draws, never on a polling loop. */
final class MusicBlurSurface extends Drawable {
    static boolean capturing;
    private final View target;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final RectF rect = new RectF();
    private final Path clip = new Path();
    private Bitmap bitmap;
    private final MusicBlurCapture capture;
    private boolean attached, geometryDirty = true;
    boolean captureVisible;
    final Rect screenBounds = new Rect();
    private final Rect visibleBounds = new Rect();
    private final RectF sourceRect = new RectF();
    private final Matrix bitmapMatrix = new Matrix();
    private final int[] position = new int[2];
    private int surface, outline;
    private float radius;
    private float segmentWidth, segmentGap;
    private final boolean allowGlass;
    private MusicGlassRenderer glass;

    MusicBlurSurface(View target, float radius) { this(target,radius,false); }
    MusicBlurSurface(View target,float radius,boolean allowGlass) { this(target,radius,allowGlass,new MusicBlurCapture(target)); }
    MusicBlurSurface(View target,float radius,boolean allowGlass,MusicBlurCapture capture) { this.target=target;this.radius=radius;this.allowGlass=allowGlass;this.capture=capture; }
    void setSegments(float controlsWidth,float gap){if(segmentWidth!=controlsWidth||segmentGap!=gap){segmentWidth=controlsWidth;segmentGap=gap;geometryDirty=true;invalidateSelf();}}
    private static volatile boolean frozen;
    public static void setFrozen(boolean value) { frozen = value; }
    static boolean isFrozen() { return frozen; }
    static boolean isCapturing() { return capturing; }
    void setColors(PlayerColors colors) {
        int fill=allowGlass?colors.surfaceHigh:colors.surface;
        if (surface == fill && outline == colors.outlineVariant) return;
        surface = fill; outline = colors.outlineVariant; capture.markDirty();
        invalidateSelf();
    }
    void attach() {
        if (attached) return;
        attached = true;capture.add(this);
    }
    void detach() {
        if (!attached) return;
        attached = false;capture.remove(this);clearCapture();
    }
    void clearCapture() {
        if (bitmap == null && glass == null) return;
        bitmap = null;if(glass!=null){glass.clear();glass=null;}invalidateSelf();
    }
    boolean updateGeometry() {
        boolean visible = target.isShown() && target.getAlpha() > 0 && target.getWidth() >= 8
                && target.getHeight() >= 8 && target.getGlobalVisibleRect(visibleBounds);
        target.getLocationOnScreen(position);
        int x=position[0], y=position[1], right=x+target.getWidth(), bottom=y+target.getHeight();
        boolean changed = captureVisible != visible || screenBounds.left != x || screenBounds.top != y
                || screenBounds.right != right || screenBounds.bottom != bottom;
        captureVisible=visible;screenBounds.set(x,y,right,bottom);
        return changed;
    }
    void acceptCapture(Bitmap result,Rect region) {
        bitmap=result;
        if(result!=null){
            float sx=result.getWidth()/(float)region.width(),sy=result.getHeight()/(float)region.height();
            sourceRect.set((screenBounds.left-region.left)*sx,(screenBounds.top-region.top)*sy,
                    (screenBounds.right-region.left)*sx,(screenBounds.bottom-region.top)*sy);
        }
        invalidateSelf();
    }
    @Override protected void onBoundsChange(Rect bounds) { geometryDirty=true; }
    @Override public void draw(Canvas canvas) {
        if(capturing)return;
        rect.set(getBounds()); if (rect.isEmpty()) return;
        if(geometryDirty){
        clip.rewind();
        float split=rect.right-segmentWidth;
        if(segmentWidth>0&&split>rect.left){
            float cardRadius = Math.min(radius, AndroidUtilities.dp(16));
            clip.addRoundRect(rect.left,rect.top,split-segmentGap,rect.bottom,cardRadius,cardRadius,Path.Direction.CW);
            clip.addRoundRect(split,rect.top,rect.right,rect.bottom,radius,radius,Path.Direction.CW);
        }else clip.addRoundRect(rect, radius, radius, Path.Direction.CW);
        geometryDirty=false;
        }
        if(allowGlass&&android.os.Build.VERSION.SDK_INT>=33&&canvas.isHardwareAccelerated()&&bitmap!=null&&!bitmap.isRecycled()
                &&LiteMode.isEnabled(LiteMode.FLAG_LIQUID_GLASS)){
            int save = canvas.save();
            canvas.clipPath(clip);
            if(glass==null)glass=new MusicGlassRenderer(target,radius);
            glass.draw(canvas,bitmap,sourceRect,getBounds(),surface,outline);
            canvas.restoreToCount(save);
            paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(AndroidUtilities.dpf2(.7f));
            paint.setColor(outline); rect.inset(.5f,.5f); canvas.drawPath(clip,paint);
            paint.setStyle(Paint.Style.FILL);
            return;
        }
        int save = canvas.save(); canvas.clipPath(clip);
        if (bitmap != null && !bitmap.isRecycled()) {
            paint.setColor(0xffffffff);
            bitmapMatrix.setRectToRect(sourceRect,rect,Matrix.ScaleToFit.FILL);
            canvas.drawBitmap(bitmap, bitmapMatrix, paint);
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
