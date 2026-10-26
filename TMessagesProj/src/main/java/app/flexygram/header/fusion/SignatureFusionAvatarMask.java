package app.flexygram.header.fusion;

import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.Shader;

/**
 * Small, bounded native alpha mask; this is NOT blur and uses no frame bitmap.
 * Intended for a container owning Telegram's EXISTING BackupImageView, not for
 * loading another copy of the avatar. Never create a second ImageReceiver.
 *
 * Usage (within a clipped pill/portrait container):
 *   int save = mask.begin(canvas, 0, 0, getWidth(), getHeight());
 *   super.dispatchDraw(canvas); // draws the existing native avatar child
 *   mask.finish(canvas, save, getWidth(), getHeight(), fadeFrom, fadeTo, rtl);
 *
 * The small saveLayer is required for true alpha transparency, including
 * translucent theme surfaces. PROFILE this 50dp-high layer on physical Android;
 * if expensive, cache the STATIC avatar+mask only upon image/size/theme changes.
 */
public final class SignatureFusionAvatarMask {
    private final Paint fadePaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private LinearGradient gradient;
    private float previousStart = Float.NaN, previousEnd = Float.NaN;
    private boolean previousRtl;

    public SignatureFusionAvatarMask() {
        fadePaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_IN));
    }

    public int begin(Canvas canvas, float l, float t, float r, float b) {
        return canvas.saveLayer(l, t, r, b, null);
    }

    /** Configure during layout so the first draw also reuses its cached shader. */
    public void prepare(float fadeStart, float fadeEnd, boolean rtl) {
        if (gradient == null || fadeStart != previousStart || fadeEnd != previousEnd || rtl != previousRtl) {
            // RTL: from transparent at left to opaque at right.
            int startColor = rtl ? 0x00FFFFFF : 0xFFFFFFFF;
            int endColor = rtl ? 0xFFFFFFFF : 0x00FFFFFF;
            float x0 = Math.min(fadeStart, fadeEnd);
            float x1 = Math.max(fadeStart, fadeEnd);
            if (x1 <= x0) x1 = x0 + 1f;
            gradient = new LinearGradient(x0, 0, x1, 0,
                    startColor, endColor, Shader.TileMode.CLAMP);
            fadePaint.setShader(gradient);
            previousStart = fadeStart;
            previousEnd = fadeEnd;
            previousRtl = rtl;
        }
    }

    /** Local x positions of fade start/end relative to the avatar panel. */
    public void finish(Canvas canvas, int saveCount, float width, float height,
                       float fadeStart, float fadeEnd, boolean rtl) {
        if (width <= 0 || height <= 0) { canvas.restoreToCount(saveCount); return; }
        prepare(fadeStart, fadeEnd, rtl);
        canvas.drawRect(0, 0, width, height, fadePaint);
        canvas.restoreToCount(saveCount);
    }
}
