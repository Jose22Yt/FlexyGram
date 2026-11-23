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
    private final MaterialShader[] shaders = new MaterialShader[RESOURCES.length];
    private final Matrix matrix = new Matrix();
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);

    void draw(Canvas canvas, float left, float top, float right, float bottom, float radius,
              Path path, boolean dark, int alpha) {
        final float width = right - left, height = bottom - top;
        final boolean circle = path == null && Math.abs(width - height) <= 1f
                && radius >= Math.min(width, height) * .5f - 1f;
        final int index = (dark ? 0 : 2) + (circle ? 1 : 0);
        MaterialShader material = shaders[index];
        if (material == null) {
            Bitmap texture = textures[index];
            if (texture == null) {
                texture = BitmapFactory.decodeResource(ApplicationLoader.applicationContext.getResources(), RESOURCES[index]);
                if (texture == null) return;
                textures[index] = texture;
            }
            material = new MaterialShader(texture);
            shaders[index] = material;
        }

        // Move round silhouettes with the canvas so scrolling does not rebuild the shader matrix.
        material.updateMatrix(matrix, width, height, path == null ? 0f : left, path == null ? 0f : top);
        if (paint.getShader() != material.shader) paint.setShader(material.shader);
        if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
        if (path != null) {
            canvas.drawPath(path, paint);
        } else {
            int save = canvas.save();
            canvas.translate(left, top);
            canvas.drawRoundRect(0f, 0f, width, height, radius, radius, paint);
            canvas.restoreToCount(save);
        }
    }

    private static final class MaterialShader {
        final BitmapShader shader;
        final int textureWidth, textureHeight;
        private float width, height, x, y;

        MaterialShader(Bitmap texture) {
            textureWidth = texture.getWidth();
            textureHeight = texture.getHeight();
            shader = new BitmapShader(texture, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
        }

        void updateMatrix(Matrix matrix, float width, float height, float x, float y) {
            if (this.width == width && this.height == height && this.x == x && this.y == y) return;
            this.width = width;
            this.height = height;
            this.x = x;
            this.y = y;
            matrix.setScale(width / textureWidth, height / textureHeight);
            matrix.postTranslate(x, y);
            shader.setLocalMatrix(matrix);
        }
    }
}
