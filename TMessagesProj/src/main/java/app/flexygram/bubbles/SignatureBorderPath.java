package app.flexygram.bubbles;

import android.graphics.Path;
import android.graphics.Shader;
import android.graphics.LinearGradient;
import android.graphics.PathMeasure;
import android.graphics.RectF;
import android.graphics.Rect;
import org.telegram.messenger.AndroidUtilities;

/** Cached pieces of the original silhouette, including curves and tails. UI thread only. */
public final class SignatureBorderPath {
    private final Path result = new Path();
    private final PathMeasure measure = new PathMeasure();
    private final RectF bounds = new RectF();
    private final float[] point = new float[2];
    private final int[] geometry = new int[11];
    private final RectF fadeBounds = new RectF();
    private final int[] fadeColors = new int[4];
    private final float[] fadeStops = new float[4];
    private Shader fadeShader;
    private int fadeRgb;
    private boolean initialized;
    private int mode = -1;

    public Path get(Path path, int position, Rect rect, int radius, int near, int small,
                    int padding, int type, int flags, int clippedTop) {
        if (position == 5) { mode = 5; return path; }
        boolean same = same(0, rect.left) & same(1, rect.top) & same(2, rect.right)
                & same(3, rect.bottom) & same(4, radius) & same(5, near) & same(6, small)
                & same(7, padding) & same(8, type) & same(9, flags) & same(10, clippedTop);
        if (initialized && same && position == mode) return result;
        initialized = true; mode = position; result.rewind(); fadeShader = null;
        if (position == 0) return result;
        path.computeBounds(bounds, true);
        measure.setPath(path, false);
        do {
            float length = measure.getLength();
            if (length <= 0) continue;
            float step = Math.max(.5f, AndroidUtilities.density * 2f);
            boolean inside = belongs(0, position);
            float start = inside ? 0 : -1;
            for (float previous = 0; previous < length;) {
                float next = Math.min(length, previous + step);
                boolean nextInside = belongs(next, position);
                if (inside != nextInside) {
                    float lo = previous, hi = next;
                    for (int n = 0; n < 10; n++) {
                        float mid = (lo + hi) * .5f;
                        if (belongs(mid, position) == inside) lo = mid; else hi = mid;
                    }
                    float edge = (lo + hi) * .5f;
                    if (inside) measure.getSegment(start, edge, result, true); else start = edge;
                    inside = nextInside;
                }
                previous = next;
            }
            if (inside) measure.getSegment(start, length, result, true);
        } while (measure.nextContour());
        result.computeBounds(fadeBounds, true);
        return result;
    }

    /** Two softly terminating ends, cached by native geometry and RGB, never by animation alpha.
     * One shader/stroke pass; no blur, layer, extra path or per-frame allocation. */
    public Shader fade(int color) {
        if (mode <= 0 || mode == 5) return null;
        int rgb = color & 0x00ffffff;
        if (fadeShader != null && fadeRgb == rgb) return fadeShader;
        fadeRgb = rgb;
        boolean horizontal = mode == 1 || mode == 2;
        float length = horizontal ? fadeBounds.width() : fadeBounds.height();
        if (length <= 0) return null;
        float taper = Math.min(.25f, AndroidUtilities.density * 6f / length);
        fadeColors[0] = fadeColors[3] = rgb;
        fadeColors[1] = fadeColors[2] = rgb | 0xff000000;
        fadeStops[0] = 0; fadeStops[1] = taper; fadeStops[2] = 1 - taper; fadeStops[3] = 1;
        fadeShader = new LinearGradient(fadeBounds.left, fadeBounds.top,
                horizontal ? fadeBounds.right : fadeBounds.left,
                horizontal ? fadeBounds.top : fadeBounds.bottom,
                fadeColors, fadeStops, Shader.TileMode.CLAMP);
        return fadeShader;
    }

    private boolean same(int index, int value) {
        boolean equal = geometry[index] == value;
        geometry[index] = value;
        return equal;
    }

    private boolean belongs(float distance, int position) {
        measure.getPosTan(distance, point, null);
        float x = (point[0] - bounds.centerX()) / Math.max(1, bounds.width());
        float y = (point[1] - bounds.centerY()) / Math.max(1, bounds.height());
        int side = Math.abs(y) >= Math.abs(x) ? (y < 0 ? 1 : 2) : (x < 0 ? 3 : 4);
        return side == position;
    }
}
