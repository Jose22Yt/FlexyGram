package app.flexygram.effects;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.BitmapShader;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Shader;

import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.R;

/** A sampled lighting layer. Only the local shape, never the chat backdrop, is textured. */
final class SatinEdgeMaterial {
    private static final int[] RESOURCES = {
            R.drawable.flexy_satin_pill_dark, R.drawable.flexy_satin_circle_dark,
            R.drawable.flexy_satin_pill_light, R.drawable.flexy_satin_circle_light
    };
    private static final Bitmap[] textures = new Bitmap[RESOURCES.length];
    private final BitmapShader[] shaders = new BitmapShader[RESOURCES.length];
    private final Matrix matrix = new Matrix();
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);

    void draw(Canvas canvas, float left, float top, float right, float bottom, float radius,
              Path path, boolean dark, int alpha) {
        final float width = right - left, height = bottom - top;
        final boolean circle = path == null && Math.abs(width - height) <= 1f
                && radius >= Math.min(width, height) * .5f - 1f;
        final int index = (dark ? 0 : 2) + (circle ? 1 : 0);
        if (textures[index] == null) {
            textures[index] = BitmapFactory.decodeResource(ApplicationLoader.applicationContext.getResources(), RESOURCES[index]);
        }
        final Bitmap texture = textures[index];
        if (shaders[index] == null) {
            shaders[index] = new BitmapShader(texture, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
        }
        matrix.setScale(width / texture.getWidth(), height / texture.getHeight());
        matrix.postTranslate(left, top);
        shaders[index].setLocalMatrix(matrix);
        paint.setShader(shaders[index]);
        paint.setAlpha(alpha);
        if (path != null) {
            canvas.drawPath(path, paint);
        } else {
            canvas.drawRoundRect(left, top, right, bottom, radius, radius, paint);
        }
    }
}
