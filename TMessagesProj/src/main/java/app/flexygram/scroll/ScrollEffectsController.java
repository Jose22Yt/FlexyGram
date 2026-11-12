/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.graphics.Camera;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.view.View;
import android.view.accessibility.AccessibilityManager;
import android.content.Context;
import androidx.recyclerview.widget.RecyclerView;

/** Fixed cylinder projection over the native list: no spring, timing, animator or idle frame loop. */
public final class ScrollEffectsController {
    private final RecyclerView list;
    private final int surface;
    private final Runnable settingsChanged;
    private final ScrollEffectGeometry geometry = new ScrollEffectGeometry();
    private final Camera camera = new Camera();
    private final Matrix matrix = new Matrix(), inverse = new Matrix();
    private Matrix inverseSource;
    private final float[] cachedTops = new float[64], cachedBottoms = new float[64];
    private final Matrix[] cachedMatrices = new Matrix[64];
    private final AccessibilityManager accessibility;
    private int cachedCount, frameWidth, frameCurvature;
    private float cameraDepth = -1;
    private float top, bottom;
    private boolean enabled;

    public ScrollEffectsController(RecyclerView list, int surface) {
        this.list = list; this.surface = surface;
        ScrollEffectsConfig.load();
        settingsChanged = list::invalidate;
        ScrollEffectsConfig.observe(settingsChanged);
        accessibility = (AccessibilityManager) list.getContext().getSystemService(Context.ACCESSIBILITY_SERVICE);
    }
    public void beginFrame(float top, float bottom) {
        cachedCount = 0; inverseSource = null;
        this.top = top; this.bottom = bottom;
        frameCurvature = ScrollEffectsConfig.curvature(); frameWidth = list.getWidth();
        // This is persistent geometry, independent of system animation duration/velocity/state.
        enabled = ScrollEffectsConfig.style(surface) == ScrollEffectsConfig.WHEEL && frameCurvature > 0
                && bottom > top && frameWidth > 0 && list.isAttachedToWindow()
                && list.getWindowVisibility() == View.VISIBLE
                && (accessibility == null || !accessibility.isTouchExplorationEnabled());
    }
    public int save(Canvas canvas, float rowTop, float rowBottom) {
        if (!enabled || rowBottom <= rowTop) return -1;
        int save = canvas.save();
        try { concat(canvas, rowTop, rowBottom); return save; }
        catch (RuntimeException | Error failure) { canvas.restoreToCount(save); throw failure; }
    }
    public void concat(Canvas canvas, float rowTop, float rowBottom) {
        if (enabled && rowBottom > rowTop) canvas.concat(matrixForBounds(rowTop, rowBottom));
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
        cached.set(matrix); return cached;
    }
    private void buildMatrix(float rowTop, float rowBottom) {
        float height = bottom - top;
        float center = (rowTop + rowBottom) * .5f;
        if (rowBottom - rowTop > height * .75f) {
            float visibleTop = Math.max(top, rowTop), visibleBottom = Math.min(bottom, rowBottom);
            float boundedCenter = visibleTop <= visibleBottom ? (visibleTop + visibleBottom) * .5f
                    : Math.max(top, Math.min(bottom, center));
            float blend = Math.min(1, ((rowBottom - rowTop) / height - .75f) * 2);
            blend = blend * blend * (3 - 2 * blend);
            center += (boundedCenter - center) * blend;
        }
        float position = (center - (top + bottom) * .5f) / (height * .5f);
        geometry.calculate(position, height, frameCurvature);
        float pivotX = frameWidth * .5f;
        float depth = Math.max(Math.max(1, frameWidth) * 3f,
                2 * Math.max(Math.abs(rowTop - center), Math.abs(rowBottom - center)));
        // Keep very tall text/media in front of the camera plane even at maximum curvature.
        if (cameraDepth != depth) {
            camera.setLocation(0, 0, -depth / 72f); cameraDepth = depth;
        }
        camera.save(); camera.rotateX(geometry.rotationX); camera.getMatrix(matrix); camera.restore();
        if (geometry.scaleX != 1) matrix.preScale(geometry.scaleX, 1f);
        matrix.preTranslate(-pivotX, -center);
        matrix.postTranslate(pivotX, center + geometry.translationY);
    }
    public boolean mapTouch(float x, float y, float rowTop, float rowBottom, float[] point) {
        if (!enabled || rowBottom <= rowTop || y < top || y > bottom) return false;
        Matrix source = matrixForBounds(rowTop, rowBottom);
        if (source == matrix || source != inverseSource) {
            if (!source.invert(inverse)) return false;
            inverseSource = source == matrix ? null : source;
        }
        point[0] = x; point[1] = y; inverse.mapPoints(point); return true;
    }
    public boolean isActive() { return enabled; }
    public long renderHash() {
        if (!enabled) return 0;
        long hash = frameCurvature;
        hash = hash * 31 + Float.floatToIntBits(top);
        hash = hash * 31 + Float.floatToIntBits(bottom);
        return hash * 31 + frameWidth;
    }
    public void reset() { enabled = false; cachedCount = 0; inverseSource = null; }
}
