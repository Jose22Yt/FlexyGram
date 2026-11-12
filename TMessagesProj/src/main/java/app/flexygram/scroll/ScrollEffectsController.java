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
    private final float[] cachedTops = new float[64], cachedBottoms = new float[64];
    private final Matrix[] cachedMatrices = new Matrix[64];
    private int cachedCount;
    private final AccessibilityManager accessibility;
    private float top, bottom, frameIntensity;
    private int style;
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
        if (!allowed() || !list.isAttachedToWindow() || list.getWindowVisibility() != View.VISIBLE) { reset(); return; }
        // Only user drag/fling: opening a chat and restoring scroll must not animate its contents.
        if (list.getScrollState() == RecyclerView.SCROLL_STATE_IDLE) return;
        motion.scroll(dy, Math.max(1, bottom - top), SystemClock.elapsedRealtimeNanos());
        list.invalidate();
    }
    public void beginFrame(float top, float bottom) {
        cachedCount = 0;
        this.top = top; this.bottom = bottom;
        style = ScrollEffectsConfig.style(surface);
        frameIntensity = ScrollEffectsConfig.intensity();
        if (!allowed() || bottom <= top || !list.isAttachedToWindow()
                || list.getWindowVisibility() != View.VISIBLE) { reset(); return; }
        enabled = motion.advance(SystemClock.elapsedRealtimeNanos());
        if (enabled) list.postInvalidateOnAnimation();
    }
    /** Bounds include a whole media group, so its background/caption/tiles share one projection. */
    public int save(Canvas canvas, float rowTop, float rowBottom) {
        if (!enabled || motion.amount() == 0 || rowBottom <= rowTop) return -1;
        int save = canvas.save();
        concat(canvas, rowTop, rowBottom);
        return save;
    }
    public void concat(Canvas canvas, float rowTop, float rowBottom) {
        if (!enabled || motion.amount() == 0 || rowBottom <= rowTop) return;
        canvas.concat(matrixForBounds(rowTop, rowBottom));
    }
    private Matrix matrixForBounds(float rowTop, float rowBottom) {
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
        // Tall messages/albums use their visible portion, never an offscreen pivot thousands of px away.
        float visibleTop = Math.max(top, rowTop), visibleBottom = Math.min(bottom, rowBottom);
        float center = visibleTop <= visibleBottom ? (visibleTop + visibleBottom) * .5f
                : Math.max(top, Math.min(bottom, (rowTop + rowBottom) * .5f));
        float position = (center - (top + bottom) * .5f) / (height * .5f);
        geometry.calculate(style, position, list.getWidth(), height,
                motion.amount(), motion.direction(), frameIntensity);
        float pivotX = list.getWidth() * .5f;
        float pivotY = style == ScrollEffectsConfig.PERSPECTIVE ? (top + bottom) * .5f : center;
        camera.save();
        // Camera depth is proportional to viewport width in pixels: equal perspective across densities.
        camera.setLocation(0, 0, -Math.max(1, list.getWidth()) * 3f / 72f);
        camera.rotateX(geometry.rotationX);
        camera.rotateY(geometry.rotationY);
        camera.rotateZ(geometry.rotationZ);
        camera.getMatrix(matrix);
        camera.restore();
        matrix.preScale(geometry.scaleX, 1f);
        matrix.preTranslate(-pivotX, -pivotY);
        matrix.postTranslate(pivotX + geometry.translationX, pivotY + geometry.translationY);
    }
    public boolean mapTouch(float x, float y, float rowTop, float rowBottom, float[] point) {
        if (!enabled || motion.amount() == 0 || rowBottom <= rowTop || y < top || y > bottom) return false;
        if (!matrixForBounds(rowTop, rowBottom).invert(inverse)) return false;
        point[0] = x; point[1] = y;
        inverse.mapPoints(point);
        return true;
    }
    public boolean isActive() { return enabled && motion.amount() != 0; }
    public long renderHash() {
        if (!isActive()) return 0;
        long hash = style;
        hash = hash * 31 + Float.floatToIntBits(motion.amount());
        hash = hash * 31 + Float.floatToIntBits(motion.direction());
        hash = hash * 31 + Float.floatToIntBits(frameIntensity);
        hash = hash * 31 + Float.floatToIntBits(top);
        hash = hash * 31 + Float.floatToIntBits(bottom);
        return hash * 31 + list.getWidth();
    }
    public void reset() { motion.reset(); enabled = false; cachedCount = 0; }
    /** Release smoothly; the list maps the initial hit and preserves raw movement deltas. */
    public void onTouchDown() { motion.stop(SystemClock.elapsedRealtimeNanos()); list.invalidate(); }
}
