package app.flexygram.effects;

import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import org.telegram.messenger.AndroidUtilities;

/** A perimeter reflection with stronger highlights at the top and bottom. */
public final class ChatEdgeReflection {
    private static final int[] DARK = {
            0x46ffffff, 0x21ffffff, 0x00ffffff, 0x00ffffff, 0x20ffffff, 0x50ffffff
    };
    private static final int[] LIGHT = {
            0x240d2237, 0x70ffffff, 0x00ffffff, 0x000d2237, 0x190d2237, 0x3b0d2237
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
    private boolean darkTheme;
    private int nextSlot;

    public ChatEdgeReflection() {
        sidePaint.setStyle(Paint.Style.STROKE);
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
        // View translations can introduce insignificant float differences in the height.
        final float shaderHeight = Math.max(1f, Math.round(height * 16f) / 16f);
        if (darkTheme != dark) {
            darkTheme = dark;
            java.util.Arrays.fill(shaders, null);
            java.util.Arrays.fill(sideShaders, null);
            nextSlot = 0;
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
            final float ramp = Math.min(.14f, AndroidUtilities.dpf2(5f) / shaderHeight);
            stops[1] = ramp * .2f;
            stops[2] = ramp;
            stops[3] = 1f - ramp;
            stops[4] = 1f - ramp * .26f;
            slot = nextSlot;
            heights[slot] = shaderHeight;
            shaders[slot] = new LinearGradient(0, 0, 0, shaderHeight, dark ? DARK : LIGHT, stops, Shader.TileMode.CLAMP);
            // The side reflection takes over as the original highlights fall off.
            sideStops[0] = ramp * .15f;
            sideStops[1] = ramp * 2f;
            sideStops[2] = 1f - sideStops[1];
            sideStops[3] = 1f - sideStops[0];
            sideShaders[slot] = new LinearGradient(0, 0, 0, shaderHeight, dark ? DARK_SIDES : LIGHT_SIDES,
                    sideStops, Shader.TileMode.CLAMP);
            nextSlot = (nextSlot + 1) % shaders.length;
        }

        if (paint.getShader() != shaders[slot]) paint.setShader(shaders[slot]);
        if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
        final float r = Math.min(radius, Math.min(height, right - left) * .5f);
        final int save = canvas.save();
        if (shape != null) {
            canvas.clipPath(shape);
            if (localShape == null) localShape = new Path();
            shape.offset(0f, -top, localShape);
        }
        canvas.translate(0, top);
        canvas.drawRoundRect(left, 0, right, height, r, r, paint);
        drawSides(canvas, left, right, height, r, shape != null, sideShaders[slot], alpha);
        canvas.restoreToCount(save);
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
