/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.icons;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import org.telegram.messenger.AndroidUtilities;

/** Telegram-iOS ChatListStatusChecksNode at rest, translated (-3,-4) into its slot.
 * The native list animator owns state changes; no extra frame loop or bitmap. */
public final class IosListCheckDrawable extends Drawable {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final boolean partial;
    private float preparedDensity = -1f;

    public IosListCheckDrawable(boolean partial) {
        this.partial = partial;
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStrokeJoin(Paint.Join.ROUND);
        paint.setColor(0xffffffff);
        prepare();
    }

    private void prepare() {
        float density = Math.max(1f, AndroidUtilities.density);
        if (preparedDensity == density) return;
        preparedDensity = density;
        float pixel = 1f / density;
        path.rewind();
        if (!partial) {
            path.moveTo(6f, 9f);
            path.lineTo(9.5f, 12.5f);
        } else {
            path.moveTo(9.5f, 12.5f);
        }
        // Upstream's completed second segment is (1 - 0.33) * 1.5.
        path.lineTo(9.5f + (7.5f - pixel) * 1.005f, 12.5f - 8f * 1.005f);
        paint.setStrokeWidth(1f + pixel);
    }

    @Override public void draw(Canvas canvas) {
        prepare();
        Rect bounds = getBounds();
        float scale = Math.min(bounds.width() / 18f, bounds.height() / 18f);
        if (scale <= 0) return;
        int save = canvas.save();
        canvas.translate(bounds.centerX() - 9f * scale, bounds.centerY() - 9f * scale);
        canvas.scale(scale, scale);
        canvas.drawPath(path, paint);
        canvas.restoreToCount(save);
    }

    @Override public int getIntrinsicWidth() { return AndroidUtilities.dp(18); }
    @Override public int getIntrinsicHeight() { return AndroidUtilities.dp(18); }
    @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
    @Override public int getAlpha() { return paint.getAlpha(); }
    @Override public void setColorFilter(ColorFilter filter) { paint.setColorFilter(filter); invalidateSelf(); }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
}
