/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.animation.ValueAnimator;
import android.graphics.Camera;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.os.SystemClock;
import android.os.Build;
import android.provider.Settings;
import android.view.View;
import android.view.accessibility.AccessibilityManager;
import android.content.Context;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.SharedConfig;

/** Canvas-only transforms: never owns item translations, layouts, bitmaps or hardware layers. */
public final class ScrollEffectsController extends RecyclerView.OnScrollListener {
    private final RecyclerView list;
    private final int surface;
    private final ScrollEffectMotion motion = new ScrollEffectMotion();
    private final ScrollEffectGeometry geometry = new ScrollEffectGeometry();
    private final Camera camera = new Camera();
    private final Matrix matrix = new Matrix();
    private final Matrix inverse = new Matrix();
    private Matrix inverseSource;
    private final float[] cachedTops = new float[64], cachedBottoms = new float[64];
    private final Matrix[] cachedMatrices = new Matrix[64];
    private int cachedCount;
    private final AccessibilityManager accessibility;
    private float top, bottom, frameIntensity, frameAmount, frameDirection;
    private int style, frameWidth, cameraWidth = -1;
    private boolean enabled;

    public ScrollEffectsController(RecyclerView list, int surface) {
        this.list = list; this.surface = surface;
        ScrollEffectsConfig.load();
        accessibility = (AccessibilityManager) list.getContext().getSystemService(Context.ACCESSIBILITY_SERVICE);
        list.addOnScrollListener(this);
    }
    private boolean allowed() {
        return ScrollEffectsConfig.style(surface) != ScrollEffectsConfig.NONE
                && SharedConfig.animationsEnabled() && (Build.VERSION.SDK_INT >= 26 ? ValueAnimator.areAnimatorsEnabled()
                    : Settings.Global.getFloat(list.getContext().getContentResolver(), Settings.Global.ANIMATOR_DURATION_SCALE, 1f) > 0)
                && (accessibility == null || !accessibility.isTouchExplorationEnabled());
    }
    @Override public void onScrolled(RecyclerView recycler, int dx, int dy) {
        if (dy == 0) return;
        if (!allowed() || !list.isAttachedToWindow() || list.getWindowVisibility() != View.VISIBLE) { reset(); return; }
        // Only user drag/fling: opening a chat and restoring scroll must not animate its contents.
        if (list.getScrollState() == RecyclerView.SCROLL_STATE_IDLE) return;
        motion.scroll(dy, Math.max(1, bottom - top), SystemClock.elapsedRealtimeNanos());
        list.invalidate();
    }
    public void beginFrame(float top, float bottom) {
        cachedCount = 0;
        inverseSource = null;
        this.top = top; this.bottom = bottom;
        style = ScrollEffectsConfig.style(surface);
        frameIntensity = ScrollEffectsConfig.intensity();
        frameWidth = list.getWidth();
        if (!allowed() || bottom <= top || !list.isAttachedToWindow()
                || list.getWindowVisibility() != View.VISIBLE) { reset(); return; }
        enabled = motion.advance(SystemClock.elapsedRealtimeNanos());
        frameAmount = motion.amount(); frameDirection = motion.direction();
        if (enabled) list.postInvalidateOnAnimation();
    }
    /** Bounds include a whole media group, so its background/caption/tiles share one projection. */
    public int save(Canvas canvas, float rowTop, float rowBottom) {
        if (!isActive() || rowBottom <= rowTop) return -1;
        int save = canvas.save();
        concat(canvas, rowTop, rowBottom);
        return save;
    }
    public void concat(Canvas canvas, float rowTop, float rowBottom) {
        if (!isActive() || rowBottom <= rowTop) return;
        canvas.concat(matrixForBounds(rowTop, rowBottom));
    }
    private Matrix matrixForBounds(float rowTop, float rowBottom) {
        // Perspective is the same projection for the entire viewport, including deferred passes.
        if (style == ScrollEffectsConfig.PERSPECTIVE) { rowTop = top; rowBottom = bottom; }
        for (int i = 0; i < cachedCount; i++) {
            if (cachedTops[i] == rowTop && cachedBottoms[i] == rowBottom) return cachedMatrices[i];
        }
        buildMatrix(rowTop, rowBottom);
        if (cachedCount == cachedMatrices.length) return matrix;
        int index = cachedCount++;
        cachedTops[index] = rowTop; cachedBottoms[index] = rowBottom;
        Matrix cached = cachedMatrices[index];
        if (cached == null) cachedMatrices[index] = cached = new Matrix();
        cached.set(matrix);
        return cached;
    }
    private void buildMatrix(float rowTop, float rowBottom) {
        float height = bottom - top;
        // A normal row keeps its own pivot as it crosses the edge: clipping must not move it.
        float center = (rowTop + rowBottom) * .5f;
        if (rowBottom - rowTop > height * .75f) {
            // Blend into the bounded pivot around viewport-sized items. A hard height switch
            // would jump the pivot as an album or long message changes size.
            float visibleTop = Math.max(top, rowTop), visibleBottom = Math.min(bottom, rowBottom);
            float boundedCenter = visibleTop <= visibleBottom ? (visibleTop + visibleBottom) * .5f
                    : Math.max(top, Math.min(bottom, center));
            float blend = Math.min(1, ((rowBottom - rowTop) / height - .75f) * 2);
            blend = blend * blend * (3 - 2 * blend);
            center += (boundedCenter - center) * blend;
        }
        float position = (center - (top + bottom) * .5f) / (height * .5f);
        geometry.calculate(style, position, frameWidth, height,
                frameAmount, frameDirection, frameIntensity);
        if (style == ScrollEffectsConfig.LATERAL) {
            matrix.setTranslate(geometry.translationX, 0);
            return;
        }
        float pivotX = frameWidth * .5f;
        float pivotY = style == ScrollEffectsConfig.PERSPECTIVE ? (top + bottom) * .5f : center;
        // Camera depth is proportional to viewport width in pixels: equal perspective across densities.
        if (cameraWidth != frameWidth) {
            camera.setLocation(0, 0, -Math.max(1, frameWidth) * 3f / 72f);
            cameraWidth = frameWidth;
        }
        camera.save();
        camera.rotateX(geometry.rotationX);
        if (geometry.rotationY != 0) camera.rotateY(geometry.rotationY);
        if (geometry.rotationZ != 0) camera.rotateZ(geometry.rotationZ);
        camera.getMatrix(matrix);
        camera.restore();
        if (geometry.scaleX != 1) matrix.preScale(geometry.scaleX, 1f);
        matrix.preTranslate(-pivotX, -pivotY);
        matrix.postTranslate(pivotX + geometry.translationX, pivotY + geometry.translationY);
    }
    public boolean mapTouch(float x, float y, float rowTop, float rowBottom, float[] point) {
        if (!isActive() || rowBottom <= rowTop || y < top || y > bottom) return false;
        Matrix source = matrixForBounds(rowTop, rowBottom);
        // The overflow scratch matrix is mutable; only retain inverses of the bounded cache.
        if (source == matrix || source != inverseSource) {
            if (!source.invert(inverse)) return false;
            inverseSource = source == matrix ? null : source;
        }
        point[0] = x; point[1] = y;
        inverse.mapPoints(point);
        return true;
    }
    public boolean isActive() { return enabled && frameAmount != 0; }
    public long renderHash() {
        if (!isActive()) return 0;
        long hash = style;
        hash = hash * 31 + Float.floatToIntBits(frameAmount);
        hash = hash * 31 + Float.floatToIntBits(frameDirection);
        hash = hash * 31 + Float.floatToIntBits(frameIntensity);
        hash = hash * 31 + Float.floatToIntBits(top);
        hash = hash * 31 + Float.floatToIntBits(bottom);
        return hash * 31 + frameWidth;
    }
    public void reset() { motion.reset(); enabled = false; frameAmount = frameDirection = 0; cachedCount = 0; inverseSource = null; }
    /** Release smoothly; the list maps the initial hit and preserves raw movement deltas. */
    public void onTouchDown() {
        if (!isActive()) return;
        motion.interrupt(SystemClock.elapsedRealtimeNanos(), frameAmount, frameDirection);
        list.invalidate();
    }
}
