package app.flexygram.effects;

import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.RuntimeShader;
import android.graphics.Shader;
import android.os.Build;

import androidx.annotation.RequiresApi;
import org.telegram.messenger.AndroidUtilities;

/** A perimeter reflection with stronger highlights at the top and bottom. */
public final class ChatEdgeReflection {
    private static final int[] DARK = {
            0x46ffffff, 0x21ffffff, 0x00ffffff, 0x00ffffff, 0x20ffffff, 0x50ffffff
    };
    private static final int[] LIGHT = {
            0x240d2237, 0x70ffffff, 0x00ffffff, 0x000d2237, 0x190d2237, 0x3b0d2237
    };
    private static final int[] SUBTLE_DARK = {
            0x24ffffff, 0x19ffffff, 0x00ffffff, 0x00ffffff, 0x16ffffff, 0x20ffffff
    };
    private static final int[] SUBTLE_LIGHT = {
            0xe8ffffff, 0x70ffffff, 0x00ffffff, 0x00474747, 0x07474747, 0x24474747
    };
    private static final int[] DARK_SIDES = {0x00ffffff, 0x48ffffff, 0x48ffffff, 0x00ffffff};
    private static final int[] LIGHT_SIDES = {0x000d2237, 0x400d2237, 0x400d2237, 0x000d2237};
    private static final float[] SIDE_BANDS = {1f, .63f, .28f};
    private static final float[] SIDE_OPACITY = {.23f, .30f, .47f};
    // A view normally uses up to four heights (including separate counters and actions).
    private final float[] heights = new float[4];
    private final float[] stops = {0f, 0f, 0f, 0f, 0f, 1f};
    private final float[] sideStops = new float[4];
    private final LinearGradient[] shaders = new LinearGradient[4];
    private final LinearGradient[] sideShaders = new LinearGradient[4];
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint sidePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private Path localShape;
    private CurvedEdge curvedEdge;
    private boolean darkTheme;
    private boolean subtle;
    private int nextSlot;

    public ChatEdgeReflection() {
        sidePaint.setStyle(Paint.Style.STROKE);
    }

    public void setSubtle(boolean subtle) {
        if (this.subtle == subtle) return;
        this.subtle = subtle;
        resetGradients();
    }

    private void resetGradients() {
        java.util.Arrays.fill(shaders, null);
        java.util.Arrays.fill(sideShaders, null);
        nextSlot = 0;
    }

    public void draw(Canvas canvas, RectF bounds, float radius, boolean dark, int alpha) {
        draw(canvas, bounds.left, bounds.top, bounds.right, bounds.bottom, radius, dark, alpha);
    }

    public void draw(Canvas canvas, float left, float top, float right, float bottom,
            float radius, boolean dark, int alpha) {
        draw(canvas, left, top, right, bottom, radius, null, dark, alpha);
    }

    public void drawClipped(Canvas canvas, float left, float top, float right, float bottom,
            Path shape, boolean dark, int alpha) {
        draw(canvas, left, top, right, bottom, 0f, shape, dark, alpha);
    }

    private void draw(Canvas canvas, float left, float top, float right, float bottom,
            float radius, Path shape, boolean dark, int alpha) {
        final float height = bottom - top;
        if (height <= 0 || right <= left || alpha == 0) return;
        final float r = Math.min(radius, Math.min(height, right - left) * .5f);
        if (subtle && shape == null && Build.VERSION.SDK_INT >= 33 && canvas.isHardwareAccelerated()) {
            if (curvedEdge == null) curvedEdge = new CurvedEdge();
            curvedEdge.draw(canvas, left, top, right - left, height, r, dark, alpha);
            return;
        }
        // View translations can introduce insignificant float differences in the height.
        final float shaderHeight = Math.max(1f, Math.round(height * 16f) / 16f);
        if (darkTheme != dark) {
            darkTheme = dark;
            resetGradients();
        }
        int slot = -1;
        for (int i = 0; i < shaders.length; i++) {
            if (heights[i] == shaderHeight && shaders[i] != null) {
                slot = i;
                break;
            }
        }
        if (slot < 0) {
            // Keep the falloff close to the edge even when the message field grows.
            final float topDepthDp = subtle ? (dark ? 4.25f : 2f) : 5f;
            final float bottomDepthDp = subtle ? (dark ? 3.4f : 1f) : 5f;
            final float topRamp = Math.min(.14f, AndroidUtilities.dpf2(topDepthDp) / shaderHeight);
            final float bottomRamp = Math.min(.14f, AndroidUtilities.dpf2(bottomDepthDp) / shaderHeight);
            stops[1] = topRamp * .2f;
            stops[2] = topRamp;
            stops[3] = 1f - bottomRamp;
            stops[4] = 1f - bottomRamp * .26f;
            slot = nextSlot;
            heights[slot] = shaderHeight;
            final int[] colors = subtle ? (dark ? SUBTLE_DARK : SUBTLE_LIGHT) : (dark ? DARK : LIGHT);
            shaders[slot] = new LinearGradient(0, 0, 0, shaderHeight, colors, stops, Shader.TileMode.CLAMP);
            if (!subtle) {
                // The side reflection takes over as the original highlights fall off.
                sideStops[0] = topRamp * .15f;
                sideStops[1] = topRamp * 2f;
                sideStops[2] = 1f - sideStops[1];
                sideStops[3] = 1f - sideStops[0];
                sideShaders[slot] = new LinearGradient(0, 0, 0, shaderHeight, dark ? DARK_SIDES : LIGHT_SIDES,
                        sideStops, Shader.TileMode.CLAMP);
            }
            nextSlot = (nextSlot + 1) % shaders.length;
        }

        if (paint.getShader() != shaders[slot]) paint.setShader(shaders[slot]);
        if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
        final int save = canvas.save();
        if (shape != null) {
            canvas.clipPath(shape);
            if (!subtle) {
                if (localShape == null) localShape = new Path();
                shape.offset(0f, -top, localShape);
            }
        }
        canvas.translate(0, top);
        canvas.drawRoundRect(left, 0, right, height, r, r, paint);
        if (!subtle) drawSides(canvas, left, right, height, r, shape != null, sideShaders[slot], alpha);
        canvas.restoreToCount(save);
    }

    @RequiresApi(33)
    private static final class CurvedEdge {
        private static final String EFFECT = """
                uniform float2 size;
                uniform float radius;
                uniform float density;
                uniform float dark;

                half4 main(float2 position) {
                    float2 centered = position - 0.5 * size;
                    float2 q = abs(centered) - (0.5 * size - radius);
                    float2 arc = max(q, float2(0.0));
                    float arcLength = length(arc);
                    float distance = arcLength + min(max(q.x, q.y), 0.0) - radius;
                    float vertical = arcLength > 0.0 ? arc.y / arcLength : step(q.x, q.y);
                    float direction = smoothstep(0.05, 0.95, vertical);
                    bool upper = centered.y < 0.0;
                    float depth = min(0.14 * size.y, density *
                            (dark > 0.5 ? (upper ? 3.7 : 4.2) : (upper ? 2.0 : 1.0)));
                    float fade = 1.0 - smoothstep(0.0, depth, max(0.0, -distance));
                    float strength = dark > 0.5 ? (upper ? 0.24 : 0.29) : (upper ? 0.90 : 0.14);
                    float opacity = strength * fade * fade * direction * direction;
                    float tone = dark > 0.5 || upper ? 1.0 : 0.2784;
                    return half4(half3(tone * opacity), half(opacity));
                }
                """;

        private final RuntimeShader shader = new RuntimeShader(EFFECT);
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private float width, height, radius = -1f, density;
        private boolean dark;

        CurvedEdge() {
            paint.setShader(shader);
        }

        void draw(Canvas canvas, float left, float top, float width, float height, float radius,
                boolean dark, int alpha) {
            if (this.width != width || this.height != height) {
                shader.setFloatUniform("size", width, height);
                this.width = width;
                this.height = height;
            }
            if (this.radius != radius) {
                shader.setFloatUniform("radius", radius);
                this.radius = radius;
            }
            final float density = AndroidUtilities.dpf2(1f);
            if (this.density != density || this.dark != dark) {
                shader.setFloatUniform("density", density);
                shader.setFloatUniform("dark", dark ? 1f : 0f);
                this.density = density;
                this.dark = dark;
            }
            if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
            final int save = canvas.save();
            canvas.translate(left, top);
            canvas.drawRoundRect(0f, 0f, width, height, radius, radius, paint);
            canvas.restoreToCount(save);
        }
    }

    private void drawSides(Canvas canvas, float left, float right, float height, float radius,
            boolean clipped, LinearGradient gradient, int alpha) {
        if (sidePaint.getShader() != gradient) sidePaint.setShader(gradient);
        final float depth = Math.min(AndroidUtilities.dpf2(5f), Math.min(height, right - left) * .14f);
        for (int i = 0; i < SIDE_BANDS.length; i++) {
            final float band = depth * SIDE_BANDS[i];
            sidePaint.setAlpha(Math.round(alpha * SIDE_OPACITY[i]));
            if (clipped) {
                sidePaint.setStrokeWidth(band * 2f);
                canvas.drawPath(localShape, sidePaint);
            } else {
                final float inset = band * .5f;
                final float r = Math.max(0f, radius - inset);
                sidePaint.setStrokeWidth(band);
                canvas.drawRoundRect(left + inset, inset, right - inset, height - inset, r, r, sidePaint);
            }
        }
    }
}
