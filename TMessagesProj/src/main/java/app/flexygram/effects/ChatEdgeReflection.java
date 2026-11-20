package app.flexygram.effects;

import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Shader;
import org.telegram.messenger.AndroidUtilities;

/** Two short vertical light ramps clipped by the existing round shape. */
public final class ChatEdgeReflection {
    private static final int[] DARK = {
            0x46ffffff, 0x21ffffff, 0x00ffffff, 0x00ffffff, 0x20ffffff, 0x50ffffff
    };
    private static final int[] LIGHT = {
            0x240d2237, 0x70ffffff, 0x00ffffff, 0x000d2237, 0x190d2237, 0x3b0d2237
    };
    // A view normally uses up to four heights (including separate counters and actions).
    private final float[] heights = new float[4];
    private final float[] stops = {0f, 0f, 0f, 0f, 0f, 1f};
    private final LinearGradient[] shaders = new LinearGradient[4];
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean darkTheme;
    private int nextSlot;

    public void draw(Canvas canvas, RectF bounds, float radius, boolean dark, int alpha) {
        draw(canvas, bounds.left, bounds.top, bounds.right, bounds.bottom, radius, dark, alpha);
    }

    public void draw(Canvas canvas, float left, float top, float right, float bottom,
            float radius, boolean dark, int alpha) {
        final float height = bottom - top;
        if (height <= 0 || right <= left || alpha == 0) return;
        // View translations can introduce insignificant float differences in the height.
        final float shaderHeight = Math.max(1f, Math.round(height * 16f) / 16f);
        if (darkTheme != dark) {
            darkTheme = dark;
            java.util.Arrays.fill(shaders, null);
            nextSlot = 0;
        }
        LinearGradient gradient = null;
        for (int i = 0; i < shaders.length; i++) {
            if (heights[i] == shaderHeight && shaders[i] != null) {
                gradient = shaders[i];
                break;
            }
        }
        if (gradient == null) {
            // Keep the falloff close to the edge even when the message field grows.
            final float ramp = Math.min(.14f, AndroidUtilities.dpf2(5f) / shaderHeight);
            stops[1] = ramp * .2f;
            stops[2] = ramp;
            stops[3] = 1f - ramp;
            stops[4] = 1f - ramp * .26f;
            gradient = new LinearGradient(0, 0, 0, shaderHeight, dark ? DARK : LIGHT, stops, Shader.TileMode.CLAMP);
            heights[nextSlot] = shaderHeight;
            shaders[nextSlot] = gradient;
            nextSlot = (nextSlot + 1) % shaders.length;
        }

        if (paint.getShader() != gradient) paint.setShader(gradient);
        if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
        final float r = Math.min(radius, Math.min(height, right - left) * .5f);
        final int save = canvas.save();
        canvas.translate(0, top);
        canvas.drawRoundRect(left, 0, right, height, r, r, paint);
        canvas.restoreToCount(save);
    }
}
