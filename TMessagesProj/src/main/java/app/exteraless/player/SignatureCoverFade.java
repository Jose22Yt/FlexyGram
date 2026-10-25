package app.exteraless.player;

import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Shader;

/** Hero overlay only: no artwork copy, blur, sampling or animation in drawing. */
final class SignatureCoverFade {
    private final Paint paint = new Paint();
    private int width, height, color;
    void update(int width, int height, int color) {
        if (this.width == width && this.height == height && this.color == color) return;
        this.width = width; this.height = height; this.color = color;
        int clear = color & 0x00ffffff;
        paint.setShader(height > 0 ? new LinearGradient(0, 0, 0, height,
                new int[]{(color & 0x00ffffff) | 0x55000000, clear, clear, color | 0xff000000},
                new float[]{0, .18f, .42f, 1}, Shader.TileMode.CLAMP) : null);
    }
    void draw(Canvas canvas) { if (width > 0 && height > 0) canvas.drawRect(0, 0, width, height, paint); }
}
