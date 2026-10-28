package app.flexygram.bubbles;

import android.graphics.Bitmap;
import android.graphics.BitmapShader;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffColorFilter;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.os.Trace;
import android.content.ComponentCallbacks2;
import app.flexygram.motion.FlexyFrameMotion;
import android.view.View;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.Utilities;
import org.telegram.ui.ChatBackgroundDrawable;
import org.telegram.ui.Components.AnimatedFileDrawable;

/** Shared source-image blur, never a screen capture. Cache bookkeeping/publication is UI-owned;
 * scaling and the bounded CPU kernel run on Telegram's existing background queue. */
public final class SignatureWallpaperBlur {
    private static final int MAX_ENTRIES = 2, MAX_EDGE = 384, RADIUS = 8;
    private static final LinkedHashMap<Key, Entry> entries = new LinkedHashMap<>(4, .75f, true);
    private static final ArrayList<WeakReference<Owner>> waiting = new ArrayList<>();
    // Counters contain no source/account identifiers. Snapshots are requested by tests only.
    private static long hits, misses, renders, cancellations, notifications, matrixUpdates;
    public static long[] diagnostics() { return new long[]{hits, misses, renders, cancellations, notifications, entries.size(), matrixUpdates}; }
    private SignatureWallpaperBlur() { }

    /** UI-owned, no periodic sweeper. Keep at most two completed images while idle.
     * Published images are never explicitly recycled: a recorded HWUI draw may still own them. */
    public static void trimMemory(int level) {
        if (level == ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN || level < ComponentCallbacks2.TRIM_MEMORY_RUNNING_LOW) return;
        Iterator<Entry> iterator = entries.values().iterator();
        while (iterator.hasNext()) {
            Entry entry = iterator.next();
            entry.owners.removeIf(reference -> reference.get() == null);
            if (entry.owners.isEmpty()) { iterator.remove(); dispose(entry); }
        }
        resumeWaiting();
    }

    private static final class Key {
        final WeakReference<Bitmap> source;
        final int identity, generation, background, dim;
        Key(Bitmap bitmap, int background, int dim) {
            source = new WeakReference<>(bitmap); identity = System.identityHashCode(bitmap);
            generation = bitmap.getGenerationId(); this.background = background; this.dim = dim;
        }
        @Override public int hashCode() { return ((identity * 31 + generation) * 31 + background) * 31 + dim; }
        @Override public boolean equals(Object value) {
            if (this == value) return true;
            if (!(value instanceof Key)) return false;
            Key other = (Key) value; Bitmap bitmap = source.get();
            return bitmap != null && bitmap == other.source.get() && generation == other.generation
                    && background == other.background && dim == other.dim;
        }
    }
    private static final class Entry {
        final Key key;
        final ArrayList<WeakReference<Owner>> owners = new ArrayList<>();
        volatile boolean canceled;
        volatile int outcome; // Diagnostic lifecycle stage only; no source/account identifiers.
        Bitmap bitmap;
        Runnable task;
        Entry(Key key) { this.key = key; }
    }
    private static void dispose(Entry entry) {
        if (entry.task != null) cancellations++;
        entry.canceled = true;
        if (entry.task != null) Utilities.globalQueue.cancelRunnable(entry.task);
        entry.task = null;
        entry.bitmap = null; // Drop our reference; do not recycle a published/recorded bitmap.
    }
    private static void sweep() {
        Iterator<Entry> iterator = entries.values().iterator();
        while (iterator.hasNext()) {
            Entry entry = iterator.next();
            entry.owners.removeIf(reference -> reference.get() == null);
            Bitmap source = entry.key.source.get();
            boolean stale = source == null || source.isRecycled() || source.getGenerationId() != entry.key.generation;
            if (entry.owners.isEmpty() && (stale || entry.bitmap == null)) { iterator.remove(); dispose(entry); }
        }
    }
    private static boolean evictIdle() {
        Iterator<Entry> iterator = entries.values().iterator();
        while (iterator.hasNext()) {
            Entry entry = iterator.next();
            if (entry.owners.isEmpty()) { iterator.remove(); dispose(entry); return true; }
        }
        return false;
    }
    private static Entry acquire(Owner owner, Bitmap source, int background, int dim) {
        sweep();
        Key key = new Key(source, background, dim);
        Entry entry = entries.get(key);
        boolean created = entry == null;
        if (created) {
            if (entries.size() >= MAX_ENTRIES && !evictIdle()) {
                if (!owner.waitingForSlot) { waiting.add(new WeakReference<>(owner)); owner.waitingForSlot = true; }
                return null; // Matte until an attached owner releases a slot; no retry timer.
            }
            misses++; entry = new Entry(key); entries.put(key, entry);
        }
        if (!created) { hits++; Trace.beginSection("Flexy.blur.cache_hit"); Trace.endSection(); }
        entry.owners.add(new WeakReference<>(owner));
        if (created) {
            Entry pending = entry;
            pending.outcome = 1;
            entry.task = () -> {
                pending.outcome = 2;
                Bitmap result = null;
                Trace.beginSection("Flexy.blur.render");
                try {
                    if (!pending.canceled && !source.isRecycled() && source.getGenerationId() == key.generation)
                        result = render(source, background, dim, pending);
                    pending.outcome = result == null ? 3 : 4;
                } catch (IllegalArgumentException | IllegalStateException | OutOfMemoryError unavailable) {
                    pending.outcome = unavailable instanceof OutOfMemoryError ? 53 : unavailable instanceof IllegalArgumentException ? 51 : 52;
                    // Optional resource boundary only. No navigation/auth exceptions are intercepted.
                } finally { Trace.endSection(); }
                Bitmap prepared = result;
                AndroidUtilities.runOnUIThread(() -> {
                    pending.task = null;
                    if (pending.canceled || entries.get(key) != pending || source.isRecycled() || source.getGenerationId() != key.generation) {
                        pending.outcome = 6;
                        if (prepared != null) prepared.recycle();
                        return;
                    }
                    if (prepared != null) pending.outcome = 7;
                    if (prepared != null) renders++;
                    pending.bitmap = prepared;
                    // Availability callbacks may detach/replace owners synchronously.
                    // Snapshot only on publication, never in the draw/scroll loop.
                    for (WeakReference<Owner> reference : new ArrayList<>(pending.owners)) {
                        Owner current = reference.get();
                        if (current != null && !current.closed && current.entry == pending) current.ready();
                    }
                });
            };
            Utilities.globalQueue.postRunnable(entry.task);
        }
        return entry;
    }

    private static void resumeWaiting() {
        if (waiting.isEmpty()) return;
        ArrayList<WeakReference<Owner>> pending = new ArrayList<>(waiting); waiting.clear();
        for (WeakReference<Owner> reference : pending) {
            Owner owner = reference.get();
            if (owner == null) continue;
            owner.waitingForSlot = false;
            if (!owner.closed && owner.sourceBitmap != null && !owner.sourceBitmap.isRecycled()) {
                owner.entry = acquire(owner, owner.sourceBitmap, owner.background, owner.dim);
                owner.ready();
            }
        }
    }

    private static Bitmap render(Bitmap source, int background, int dim, Entry entry) {
        float scale = Math.min(1f, MAX_EDGE / (float) Math.max(source.getWidth(), source.getHeight()));
        int width = Math.max(1, Math.round(source.getWidth() * scale));
        int height = Math.max(1, Math.round(source.getHeight() * scale));
        Bitmap result = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        boolean handedOff = false;
        try {
            if (entry.canceled) return null;
            Canvas canvas = new Canvas(result); canvas.drawColor(background | 0xff000000);
            Paint paint = new Paint(Paint.FILTER_BITMAP_FLAG);
            if (dim != 0) paint.setColorFilter(new PorterDuffColorFilter(Color.argb(dim, 0, 0, 0), PorterDuff.Mode.DARKEN));
            canvas.drawBitmap(source, null, new RectF(0, 0, width, height), paint);
            if (entry.canceled) return null;
            int[] pixels = new int[width * height], scratch = new int[pixels.length];
            result.getPixels(pixels, 0, width, 0, 0, width, height);
            if (!box(pixels, scratch, width, height, true, entry)
                    || !box(scratch, pixels, width, height, false, entry)) return null;
            result.setPixels(pixels, 0, width, 0, 0, width, height);
            handedOff = true; return result;
        } finally { if (!handedOff) result.recycle(); }
    }
    private static boolean box(int[] source, int[] target, int width, int height, boolean horizontal, Entry entry) {
        int lines = horizontal ? height : width, length = horizontal ? width : height, divisor = RADIUS * 2 + 1;
        for (int line = 0; line < lines; line++) {
            if (entry.canceled) return false;
            int red = 0, green = 0, blue = 0;
            for (int j = -RADIUS; j <= RADIUS; j++) {
                int position = Math.max(0, Math.min(length - 1, j));
                int color = source[horizontal ? line * width + position : position * width + line];
                red += Color.red(color); green += Color.green(color); blue += Color.blue(color);
            }
            for (int position = 0; position < length; position++) {
                target[horizontal ? line * width + position : position * width + line] = Color.rgb(red / divisor, green / divisor, blue / divisor);
                int remove = Math.max(0, position - RADIUS), add = Math.min(length - 1, position + RADIUS + 1);
                int old = source[horizontal ? line * width + remove : remove * width + line];
                int next = source[horizontal ? line * width + add : add * width + line];
                red += Color.red(next) - Color.red(old); green += Color.green(next) - Color.green(old); blue += Color.blue(next) - Color.blue(old);
            }
        }
        return true;
    }

    /** One per attached conversation/preview. No message retains a bitmap, shader or owner. */
    public static final class Owner {
        private final WeakReference<View> target;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        private final Matrix matrix = new Matrix();
        private final RectF mapping = new RectF();
        private Drawable source;
        private Bitmap sourceBitmap;
        private int generation, background, dim;
        private Entry entry;
        private boolean closed, supported, waitingForSlot;
        private BitmapShader shader;
        private Runnable availabilityChanged;
        private FlexyFrameMotion revealMotion;
        private float reveal = 1;
        private boolean sawFallback, firstDraw;
        private float mappedLeft = Float.NaN, mappedTop, mappedWidth, mappedHeight;
        public Owner(View target) { this(target, null); }
        public Owner(View target, Runnable availabilityChanged) {
            this.target = new WeakReference<>(target);
            this.availabilityChanged = availabilityChanged;
        }

        private Bitmap bitmap(Drawable drawable) {
            if (drawable instanceof AnimatedFileDrawable) return null;
            if (drawable instanceof BitmapDrawable) {
                BitmapDrawable image = (BitmapDrawable) drawable;
                if (image.getTileModeX() != null || image.getTileModeY() != null
                        || image.getAlpha() != 255 || image.getColorFilter() != null) return null;
                mapping.set(image.getBounds());
                return image.getBitmap();
            }
            if (drawable instanceof ChatBackgroundDrawable)
                return ((ChatBackgroundDrawable) drawable).getSignatureStaticBitmap(mapping);
            return null;
        }
        public void prepare(Drawable drawable, boolean motion, int backgroundColor) {
            if (closed) return;
            if (!BubbleConfig.backgroundBlur() && entry == null && source == null) return;
            Bitmap bitmap = !motion && BubbleConfig.backgroundBlur() ? bitmap(drawable) : null;
            if (bitmap == null || bitmap.isRecycled() || (Build.VERSION.SDK_INT >= 26 && bitmap.getConfig() == Bitmap.Config.HARDWARE)) {
                clear(); supported = false; return;
            }
            int dimAlpha = drawable instanceof ChatBackgroundDrawable
                    ? Math.max(0, Math.min(255, Math.round(((ChatBackgroundDrawable) drawable).getDimAmount() * 255))) : 0;
            source = drawable; supported = true;
            if (sourceBitmap == bitmap && generation == bitmap.getGenerationId() && background == backgroundColor && dim == dimAlpha) return;
            boolean wasReady = isReady();
            release(); source = drawable; sourceBitmap = bitmap; generation = bitmap.getGenerationId(); background = backgroundColor; dim = dimAlpha;
            entry = acquire(this, bitmap, backgroundColor, dimAlpha);
            ready();
            if (wasReady && !isReady()) invalidateVisual();
        }
        private void invalidateVisual() {
            if (closed) return;
            View view = target.get();
            if (view == null) return;
            notifications++;
            if (availabilityChanged != null) availabilityChanged.run(); else view.invalidate();
        }
        private void ready() {
            if (closed || entry == null || entry.bitmap == null || entry.bitmap.isRecycled() || shader != null) return;
            Trace.beginSection("Flexy.blur.available"); Trace.endSection();
            shader = new BitmapShader(entry.bitmap, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
            paint.setShader(shader); mappedLeft = Float.NaN;
            View view = target.get();
            if (sawFallback && view != null && view.isAttachedToWindow() && view.isShown()) {
                // A genuinely cold source is revealed on the existing active-only clock, never
                // by delaying navigation or starting an independent/per-message animation.
                reveal = 0;
                revealMotion = new FlexyFrameMotion(view, 0, value -> { reveal = value; invalidateVisual(); });
                revealMotion.animateTimedTo(1, 120, null);
            } else reveal = 1; // Warm reuse is final from its very first draw.
            invalidateVisual();
        }
        public boolean isReady() { return !closed && shader != null && entry != null && entry.bitmap != null && !entry.bitmap.isRecycled(); }
        public boolean isSupported() { return supported; }
        public boolean draw(Canvas canvas, Path shape, float rootOffsetX, float rootOffsetY) {
            return draw(canvas, shape, rootOffsetX, rootOffsetY, 255);
        }
        public boolean draw(Canvas canvas, Path shape, float rootOffsetX, float rootOffsetY, int alpha) {
            // Mapping is captured once by the wallpaper owner after its native draw. A shared
            // Drawable can be drawn by another screen; never read its mutable bounds per message.
            if (!BubbleConfig.backgroundBlur() || !supported) return false;
            if (!firstDraw) {
                firstDraw = true;
                Trace.beginSection(isReady() ? "Flexy.blur.first_draw.ready" : "Flexy.blur.first_draw.fallback"); Trace.endSection();
            }
            if (!isReady()) { sawFallback = true; return false; }
            if (sourceBitmap == null || sourceBitmap.isRecycled() || sourceBitmap.getGenerationId() != generation || mapping.isEmpty()) return false;
            float left = mapping.left - rootOffsetX, top = mapping.top - rootOffsetY;
            if (mappedLeft != left || mappedTop != top || mappedWidth != mapping.width() || mappedHeight != mapping.height()) {
                matrixUpdates++;
                mappedLeft = left; mappedTop = top; mappedWidth = mapping.width(); mappedHeight = mapping.height();
                matrix.setScale(mappedWidth / entry.bitmap.getWidth(), mappedHeight / entry.bitmap.getHeight());
                matrix.postTranslate(left, top); shader.setLocalMatrix(matrix);
            }
            paint.setAlpha(Math.round(Math.max(0, Math.min(255, alpha)) * reveal));
            canvas.drawPath(shape, paint); return true;
        }
        private void release() {
            boolean freed = false;
            if (revealMotion != null) { revealMotion.dispose(); revealMotion = null; }
            sawFallback = false; firstDraw = false; reveal = 1;
            if (waitingForSlot) { waiting.removeIf(reference -> reference.get() == null || reference.get() == this); waitingForSlot = false; }
            if (shader != null) { paint.setShader(null); shader = null; }
            if (entry != null) {
                Entry previous = entry; entry = null;
                previous.owners.removeIf(reference -> reference.get() == null || reference.get() == this);
                if (previous.owners.isEmpty()) {
                    freed = true;
                    // Completed results remain in the bounded LRU. Work with no recipient is canceled.
                    if (previous.bitmap == null) { entries.remove(previous.key); dispose(previous); }
                }
            }
            sourceBitmap = null;
            if (freed) resumeWaiting();
        }
        private void clear() {
            boolean wasReady = isReady();
            release(); source = null; supported = false;
            if (wasReady) invalidateVisual();
        }
        public void close() { if (closed) return; closed = true; clear(); availabilityChanged = null; target.clear(); }
    }
}
