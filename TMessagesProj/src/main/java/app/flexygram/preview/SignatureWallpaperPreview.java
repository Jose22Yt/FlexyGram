package app.flexygram.preview;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.view.View;
import java.lang.ref.WeakReference;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.Utilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ChatBackgroundDrawable;
import org.telegram.ui.Components.AnimatedFileDrawable;
import org.telegram.ui.Components.MotionBackgroundDrawable;

/** Still wallpaper shared by settings previews. No decoding, animation loop or global observer. */
public final class SignatureWallpaperPreview {
    private final View view;
    private final Runnable changed;
    private final WeakReference<Drawable> contextual;
    private final Rect bounds = new Rect();
    private Drawable drawable;
    private Bitmap owned;
    private Runnable task;
    private int generation;
    private boolean attached;

    public SignatureWallpaperPreview(View view, Drawable contextual, Runnable changed) {
        this.view = view; this.changed = changed;
        this.contextual = new WeakReference<>(contextual);
    }
    public Drawable drawable() { return drawable; }
    public void attach() { attached = true; refresh(); }
    public void refresh() {
        int token = ++generation;
        if (task != null) { Utilities.globalQueue.cancelRunnable(task); task = null; }
        Drawable source = contextual.get();
        if (source == null) source = Theme.getCachedWallpaperNonBlocking();
        if (source == null) {
            Theme.loadWallpaper(true); // Native asynchronous loader also supplies the default wallpaper.
            publish(null, null); return;
        }
        final int shade = source instanceof ChatBackgroundDrawable
                ? Math.max(0, Math.min(255, Math.round(((ChatBackgroundDrawable) source).getDimAmount() * 255))) : 0;
        if (source instanceof ChatBackgroundDrawable) source = ((ChatBackgroundDrawable) source).getDrawable(false);
        Bitmap frame = source instanceof MotionBackgroundDrawable ? ((MotionBackgroundDrawable) source).getBitmap()
                : source instanceof AnimatedFileDrawable ? ((AnimatedFileDrawable) source).getAnimatedBitmap()
                : shade > 0 && source instanceof BitmapDrawable ? ((BitmapDrawable) source).getBitmap() : null;
        if (source instanceof MotionBackgroundDrawable || source instanceof AnimatedFileDrawable || shade > 0) {
            // Freeze one bounded frame off the UI thread; never attach or start the source renderer.
            publish(null, null);
            if (!attached || frame == null || frame.isRecycled()) return;
            task = () -> {
                Bitmap snapshot = null;
                try {
                    float scale = Math.min(1f, 512f / Math.max(frame.getWidth(), frame.getHeight()));
                    int w = Math.max(1, Math.round(frame.getWidth() * scale));
                    int h = Math.max(1, Math.round(frame.getHeight() * scale));
                    snapshot = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
                    Canvas canvas = new Canvas(snapshot);
                    canvas.drawBitmap(frame, null, new Rect(0, 0, w, h), new Paint(Paint.FILTER_BITMAP_FLAG));
                    if (shade > 0) canvas.drawColor(android.graphics.Color.argb(shade, 0, 0, 0));
                } catch (IllegalArgumentException | IllegalStateException | OutOfMemoryError unavailable) {
                    if (snapshot != null) snapshot.recycle(); snapshot = null;
                }
                Bitmap ready = snapshot;
                AndroidUtilities.runOnUIThread(() -> {
                    if (!attached || token != generation) { if (ready != null) ready.recycle(); return; }
                    task = null;
                    publish(ready == null ? null : new BitmapDrawable(view.getResources(), ready), ready);
                });
            };
            Utilities.globalQueue.postRunnable(task);
            return;
        }
        Drawable still = source != null && source.getConstantState() != null
                ? source.getConstantState().newDrawable(view.getResources()).mutate() : null;
        if (still instanceof BitmapDrawable) ((BitmapDrawable) still).setFilterBitmap(true);
        publish(still, null);
    }
    private void publish(Drawable next, Bitmap bitmap) {
        Bitmap previous = owned;
        drawable = next; owned = bitmap;
        resize(view.getWidth(), view.getHeight());
        changed.run();
        if (previous != null && previous != bitmap) previous.recycle();
    }
    public void resize(int width, int height) {
        if (drawable == null || width <= 0 || height <= 0) return;
        int iw = drawable.getIntrinsicWidth(), ih = drawable.getIntrinsicHeight();
        if (iw > 0 && ih > 0) {
            float scale = Math.max((float) width / iw, (float) height / ih);
            int w = (int) Math.ceil(iw * scale), h = (int) Math.ceil(ih * scale);
            bounds.set((width - w) / 2, (height - h) / 2, (width + w) / 2, (height + h) / 2);
        } else bounds.set(0, 0, width, height);
        drawable.setBounds(bounds);
    }
    public void draw(Canvas canvas) {
        if (drawable instanceof BitmapDrawable && ((BitmapDrawable) drawable).getBitmap().isRecycled()) return;
        if (drawable != null) drawable.draw(canvas);
    }
    public void close() {
        attached = false; generation++;
        if (task != null) Utilities.globalQueue.cancelRunnable(task);
        task = null; drawable = null;
        if (owned != null) { owned.recycle(); owned = null; }
    }
}
