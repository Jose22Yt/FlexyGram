package app.flexygram.composer;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import org.telegram.messenger.AndroidUtilities;

/** Paint only. SeekBar retains native touch, keyboard, RTL and accessibility handling. */
public final class ComposerSliderTrack extends Drawable {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float fraction;
    private int active, inactive;
    public void configure(int active, int inactive) {
        this.active = active; this.inactive = inactive; invalidateSelf();
    }
    public void setFraction(int progress, int max) {
        fraction = Math.max(0, Math.min(1, max == 0 ? 0 : progress / (float) max)); invalidateSelf();
    }
    @Override public void draw(Canvas canvas) {
        Rect b = getBounds();
        float half = AndroidUtilities.dp(7), gap = AndroidUtilities.dp(8);
        float y = b.exactCenterY(), x = b.left + b.width() * fraction;
        paint.setColor(active);
        if (x - gap > b.left) canvas.drawRoundRect(b.left, y-half, x-gap, y+half, half, half, paint);
        paint.setColor(inactive);
        if (x + gap < b.right) canvas.drawRoundRect(x+gap, y-half, b.right, y+half, half, half, paint);
    }
    @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter filter) { paint.setColorFilter(filter); invalidateSelf(); }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
}
